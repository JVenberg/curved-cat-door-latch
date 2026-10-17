"""Curved cat door latch: a strike face plate plus an arc-shaped catch arm.

Plan-view frame: hinge pin axis at the origin, Z up, latch bolt centerline at Z=0.
The closed door lies along +X and swings toward +Y. All dimensions in mm.

Run: uv run --with build123d python cat_door_latch.py
"""

from dataclasses import dataclass
from math import acos, asin, atan2, cos, degrees, hypot, radians, sin
from pathlib import Path

from build123d import (
    Axis,
    Face,
    Location,
    Plane,
    Solid,
    Vector,
    Wire,
    export_step,
    export_stl,
)

IN = 25.4


@dataclass
class P:
    # Door and hinge
    door_width: float = 28 * IN
    door_thickness: float = 35.0
    latch_gap: float = 5.0  # door latch edge to strike face; ~3 mm measured past the 2 mm test plate
    pin_offset: float = 17.1  # hinge pivot straight out from the door's room-side face (measured)
    # Latch bolt, centered in the door thickness
    bolt_throw: float = 12.7
    bolt_width: float = 15.0  # along the door thickness
    bolt_height: float = 25.0
    # Lock jamb, stop and casing on the swing side
    jamb_depth: float = 4.5625 * IN
    jamb_thickness: float = 0.75 * IN
    stop_width: float = 1.25 * IN
    stop_projection: float = 0.5 * IN
    casing_reveal: float = 5.0  # setback of casing from the strike face
    casing_width: float = 2.25 * IN
    casing_thickness: float = 17.0
    # Strike plate recess (metal strike removed, printed plate drops in)
    recess_w: float = 33.2  # across the jamb
    recess_h: float = 57.4
    recess_depth: float = 1.0
    recess_corner_r: float = 5.0  # stop-side corners
    recess_to_casing_face: float = 15.7  # recess room-side edge to the casing's front face
    latch_hole_w: float = 20.0  # across the jamb, centered on the bolt
    latch_hole_h: float = 26.0
    hole_from_room_edge: float = 10.0  # recess room-side edge to latch hole
    screw_from_room_edge: float = 19.33
    screw_spacing: float = 41.0
    # Face plate
    swing_clear: float = 1.0  # door's farthest corner to the plate and arm face; sets plate thickness
    plate_corner_r: float = 5.0
    fit_clear: float = 0.5  # per side, pad to strike recess
    wood_screw_d: float = 4.2
    wood_screw_csk_d: float = 8.4
    # Bolted joint between plate tail and arm root (M3)
    joint_edge: float = 7.0  # bolt center to joint end
    reveal_clear: float = 0.2  # arm root fills the reveal and bears on the casing and jamb edge
    root_gap: float = 1.5  # arm root end stops short of the jamb edge
    paint_fillet_r: float = 1.5  # paint build-up where the casing meets the jamb edge
    m3_clear: float = 3.4
    m3_nut_af: float = 5.8  # nut pocket in the plate front, opens upward when printed
    m3_nut_t: float = 2.4
    m3_head_d: float = 6.0
    m3_screw_len: float = 8.0
    nut_floor: float = 1.5  # plate behind the nearest nut; sets how far out the bolts sit
    bolt_pitch_s: float = 12.0
    m3_tip_clear: float = 0.3  # screw tip stops short of the plate front
    bolt_z: float = 17.0
    # Arm
    arm_thickness: float = 6.0
    slot_len: float = 17.0
    slot_height: float = 37.0
    slot_chamfer: float = 2.5
    slot_s: float = 173.0  # arc distance from closed bolt to the slot (matches original slot 2)
    end_margin: float = 24.0
    end_ramp_len: float = 20.0
    end_ramp_depth: float = 9.0  # tip lands on the bolt's bevel, past its 6.7 mm square face
    end_tip_wall: float = 2.0
    fit_gap: float = 0.3

    @property
    def strike_x(self):
        return self.door_width + self.latch_gap

    @property
    def height(self):
        return self.recess_h - 2 * self.fit_clear

    @property
    def door_face_y(self):
        return -self.pin_offset

    @property
    def stop_y(self):
        return self.door_face_y - self.door_thickness

    @property
    def bolt_y(self):
        return self.door_face_y - self.door_thickness / 2

    @property
    def recess_y(self):
        """(stop-side y, room-side y) of the strike recess."""
        y1 = self.latch_hole_y + self.latch_hole_w / 2 + self.hole_from_room_edge
        return y1 - self.recess_w, y1

    @property
    def jamb_edge_y(self):
        return self.recess_y[1] + self.recess_to_casing_face - self.casing_thickness

    @property
    def latch_hole_y(self):
        return self.bolt_y

    @property
    def r_in(self):
        return hypot(self.door_width, self.stop_y) + self.swing_clear

    @property
    def a_bolt(self):
        return atan2(self.bolt_y, self.strike_x)

    def ang(self, s):
        """Polar angle (rad) of arc length s past the closed bolt, measured on r_in."""
        return self.a_bolt + s / self.r_in

    def s_at_y(self, y):
        return (asin(y / self.r_in) - self.a_bolt) * self.r_in


def band(r0, r1, a0, a1, h, z0=None):
    """Annular sector about the hinge axis, angles in radians."""
    z0 = -h / 2 if z0 is None else z0
    span = degrees(a1 - a0)
    outer = Solid.make_cylinder(r1, h, Plane.XY.offset(z0), span)
    inner = Solid.make_cylinder(r0, h, Plane.XY.offset(z0), span)
    return (outer - inner).rotate(Axis.Z, degrees(a0))


def prism(pts, z0, h):
    face = Face(Wire.make_polygon([Vector(x, y, z0) for x, y in pts], close=True))
    return Solid.extrude(face, Vector(0, 0, h))


def polar(r, a):
    return (r * cos(a), r * sin(a))


def radial_cyl(p, s, z, r_start, length, d):
    a = p.ang(s)
    d_hat = Vector(cos(a), sin(a), 0)
    origin = Vector(r_start * cos(a), r_start * sin(a), z)
    return Solid.make_cylinder(d / 2, length, Plane(origin=origin, z_dir=d_hat))


def radial_hex(p, s, z, r_start, depth, af):
    a = p.ang(s)
    pl = Plane(origin=(r_start * cos(a), r_start * sin(a), z), x_dir=(0, 0, 1), z_dir=(cos(a), sin(a), 0))
    rc = af / 3**0.5
    pts = [pl.from_local_coords((rc * cos(radians(60 * i)), rc * sin(radians(60 * i)))) for i in range(6)]
    face = Face(Wire.make_polygon([Vector(*q) for q in pts], close=True))
    return Solid.extrude(face, Vector(cos(a), sin(a), 0) * depth)


def sector_cut(p, s0, s1, z0, z1, r0, r1):
    return band(r0, r1, p.ang(s0), p.ang(s1), z1 - z0, z0)


def joint_stations(p):
    s_joint = p.s_at_y(p.jamb_edge_y)
    t_need = p.m3_nut_t + 0.1 + p.nut_floor
    s_thick = (acos(p.strike_x / (p.r_in + t_need)) - p.a_bolt) * p.r_in
    s_bolt = max(s_thick, p.s_at_y(p.jamb_edge_y + p.casing_thickness + p.m3_head_d / 2 + 1))
    s_tail = s_bolt + p.bolt_pitch_s + p.joint_edge
    holes = [(s_bolt + ds, z) for ds in (0, p.bolt_pitch_s) for z in (-p.bolt_z, p.bolt_z)]
    return s_joint, s_tail, holes


def rounded_box(x0, x1, y0, y1, h, r):
    """Box spanning x0..x1, y0..y1, centered on Z=0, with its two y0 edges rounded."""
    box = Solid.make_box(x1 - x0, y1 - y0, h, Plane.XY.offset(-h / 2)).moved(Location((x0, y0, 0)))
    return box.fillet(r, box.edges().filter_by(Axis.X).group_by(Axis.Y)[0])


def recess_solid(p, clear=0.0, x_front=None):
    y0, y1 = p.recess_y
    x_front = p.strike_x if x_front is None else x_front
    return rounded_box(x_front, p.strike_x + p.recess_depth, y0 + clear, y1 - clear, p.recess_h - 2 * clear,
                       p.recess_corner_r - clear)


def latch_hole(p, x0, x1, grow=0.0):
    w, hh = p.latch_hole_w + 2 * grow, p.latch_hole_h + 2 * grow
    return Solid.make_box(x1 - x0, w, hh, Plane.XY.offset(-hh / 2)).moved(Location((x0, p.latch_hole_y - w / 2, 0)))


def behind(x_max, h=200):
    """Half-space x <= x_max, clipped to a generous region around the strike."""
    return Solid.make_box(x_max - 600, 600, h, Plane.XY.offset(-h / 2)).moved(Location((600, -300, 0)))


def make_plate(p):
    h, r0, c = p.height, p.r_in, p.fit_clear
    y0, _ = p.recess_y
    s_joint, s_tail, holes = joint_stations(p)
    x_back = p.strike_x

    body = rounded_box(x_back - 30, x_back, y0 + c, 300, h, p.plate_corner_r)
    plate = body & band(r0, r0 + 30, p.ang(p.s_at_y(y0) - 5), p.ang(s_tail), h)

    plate -= latch_hole(p, x_back - 30, x_back + 5, grow=0.5)
    y_screw = p.recess_y[1] - p.screw_from_room_edge
    x_front = (r0**2 - y_screw**2) ** 0.5
    for z in (-p.screw_spacing / 2, p.screw_spacing / 2):
        plate -= Solid.make_cylinder(p.wood_screw_d / 2, 30, Plane(origin=(x_back - 20, y_screw, z), z_dir=(1, 0, 0)))
        plate -= Solid.make_cone(p.wood_screw_csk_d / 2 + 1, 0, p.wood_screw_csk_d / 2 + 1,
                                 Plane(origin=(x_front - 1, y_screw, z), z_dir=(1, 0, 0)))
    for s, z in holes:
        plate -= radial_cyl(p, s, z, r0 - 1, 40, p.m3_clear)
        plate -= radial_hex(p, s, z, r0 - 1, p.m3_nut_t + 1.1, p.m3_nut_af)
    return plate


def make_arm(p):
    h, r0 = p.height, p.r_in
    s_joint, s_tail, holes = joint_stations(p)
    s_main = s_tail + p.fit_gap
    s_end = p.slot_s + p.slot_len / 2 + p.end_margin
    x_root = p.strike_x
    x_out = p.strike_x + p.casing_reveal - p.reveal_clear

    arm = band(r0, r0 + 30, p.ang(s_joint), p.ang(s_main), h) & behind(x_out) - behind(x_root)
    arm += band(r0, r0 + 30, p.ang(s_main), p.ang(s_main + 6), h) & behind(x_out)
    arm += band(r0, r0 + p.arm_thickness, p.ang(s_main), p.ang(s_end), h)
    a6 = p.ang(s_main + 6)
    taper = [polar(r0 + p.arm_thickness - 0.01, a6), polar(x_out / cos(a6), a6),
             polar(r0 + p.arm_thickness - 0.01, p.ang(s_main + 30))]
    arm += prism(taper, -h / 2, h)
    r = p.paint_fillet_r
    y_c = p.jamb_edge_y + p.root_gap
    arm -= Solid.make_box(20, 50, h + 2, Plane.XY.offset(-h / 2 - 1)).moved(Location((x_root - 10, y_c - 50, 0)))
    corner = Solid.make_box(r + 1, r + 1, h + 2, Plane.XY.offset(-h / 2 - 1)).moved(Location((x_out - r, y_c - 1, 0)))
    arm -= corner - Solid.make_cylinder(r, h + 2, Plane.XY.offset(-h / 2 - 1)).moved(Location((x_out - r, y_c + r, 0)))

    for s in (p.slot_s,):
        arm -= sector_cut(p, s - p.slot_len / 2, s + p.slot_len / 2, -p.slot_height / 2, p.slot_height / 2, r0 - 1, r0 + 20)
        c = p.slot_chamfer
        a_edge, a_back = p.ang(s - p.slot_len / 2), p.ang(s - p.slot_len / 2 - c)
        wedge = [polar(r0 - 1, a_back - 1 / r0), polar(r0 + c, a_edge), polar(r0 - 1, a_edge)]
        arm -= prism(wedge, -p.slot_height / 2, p.slot_height)

    a_end = p.ang(s_end)
    a_ramp = p.ang(s_end - p.end_ramp_len)
    flare = [polar(r0 + p.arm_thickness - 0.01, a_ramp), polar(r0 + p.end_ramp_depth + p.end_tip_wall, a_end),
             polar(r0 + p.arm_thickness - 0.01, a_end)]
    arm += prism(flare, -h / 2, h)
    ramp = [polar(r0 - 1, p.ang(s_end - p.end_ramp_len)), polar(r0 + p.end_ramp_depth, a_end + 0.5 / r0),
            polar(r0 - 1, a_end + 0.5 / r0)]
    arm -= prism(ramp, -h, 2 * h)

    for s, z in holes:
        arm -= radial_cyl(p, s, z, r0 - 1, 40, p.m3_clear)
        r_seat = r0 + p.m3_tip_clear + p.m3_screw_len
        arm -= radial_cyl(p, s, z, r_seat, 20, p.m3_head_d)
    return arm


def make_door(p, open_deg=0.0, bolt_out=True, view_h=300):
    x0 = p.strike_x - p.latch_gap
    y1 = p.door_face_y
    door = prism([(x0 - 400, y1 - p.door_thickness), (x0, y1 - p.door_thickness), (x0, y1), (x0 - 400, y1)], -view_h / 2, view_h)
    if bolt_out:
        by0 = p.bolt_y - p.bolt_width / 2
        bevel = 6.0  # leading (stop-side) corner is beveled for closing
        bolt = prism([(x0 - 1, by0), (x0 + p.bolt_throw - bevel, by0), (x0 + p.bolt_throw, by0 + bevel),
                      (x0 + p.bolt_throw, by0 + p.bolt_width), (x0 - 1, by0 + p.bolt_width)],
                     -p.bolt_height / 2, p.bolt_height)
        door += bolt
    return door.rotate(Axis.Z, open_deg)


def make_jamb(p, view_h=300):
    x, y = p.strike_x, p.jamb_edge_y
    jamb = prism([(x, y - p.jamb_depth), (x + p.jamb_thickness, y - p.jamb_depth), (x + p.jamb_thickness, y), (x, y)], -view_h / 2, view_h)
    ys = p.door_face_y - p.door_thickness
    jamb += prism([(x - p.stop_projection, ys - p.stop_width), (x, ys - p.stop_width), (x, ys), (x - p.stop_projection, ys)], -view_h / 2, view_h)
    return jamb - recess_solid(p, x_front=p.strike_x - 0.1) - latch_hole(p, p.strike_x - 0.1, p.strike_x + 16)


def make_casing(p, view_h=300):
    x, y = p.strike_x + p.casing_reveal, p.jamb_edge_y
    return prism([(x, y), (x + p.casing_width, y), (x + p.casing_width, y + p.casing_thickness), (x, y + p.casing_thickness)], -view_h / 2, view_h)


def overlap(a, b):
    r = a & b
    return 0.0 if r is None else r.volume


def check(p, plate, arm):
    parts = plate + arm
    report = []
    worst = 0.0
    for deg in [0, 0.5, 1, 2, 4, 8, 12, 16, 20, 25, 30, 40]:
        v = overlap(make_door(p, deg, bolt_out=False), parts)
        worst = max(worst, v)
    report.append(f"door (bolt retracted) sweep 0-40 deg vs parts overlap: {worst:.3f} mm^3")
    report.append(f"closed door, bolt out vs plate: {overlap(make_door(p, 0), plate):.3f} mm^3")
    for name, s in (("slot", p.slot_s),):
        deg = degrees(s / p.r_in)
        v = overlap(make_door(p, deg), parts)
        report.append(f"{name}: door open {deg:.1f} deg, bolt in slot, overlap {v:.3f} mm^3")
    report.append(f"jamb vs parts: {overlap(make_jamb(p), parts):.3f} mm^3")
    report.append(f"casing vs parts: {overlap(make_casing(p), parts):.3f} mm^3")
    return report


def main():
    p = P()
    out = Path(__file__).parent / "out"
    out.mkdir(exist_ok=True)
    plate, arm = make_plate(p), make_arm(p)
    slot_deg = degrees(p.slot_s / p.r_in)

    export_step(plate, str(out / "face_plate.step"))
    export_step(arm, str(out / "latch_arm.step"))
    export_step(make_door(p, slot_deg), str(out / "ref_door_at_slot.step"))
    export_step(make_jamb(p), str(out / "ref_lock_jamb.step"))
    export_step(make_casing(p), str(out / "ref_casing.step"))

    # Plate prints on its flat back; the arm prints standing on its lower edge.
    export_stl(plate, str(out / "face_plate.stl"))
    export_stl(arm, str(out / "latch_arm.stl"))

    print(f"arc radius (plate/arm inner face): {p.r_in:.1f} mm")
    print(f"slot at door opening {slot_deg:.1f} deg")
    for line in check(p, plate, arm):
        print(line)


if __name__ == "__main__":
    main()
