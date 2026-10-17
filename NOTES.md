# Design notes

## Coordinate frame

These are plan-view coordinates, in mm.

- The hinge pivot (the axis of rotation, not the edge of the hinge barrel) is at the origin.
- The closed door lies along +X and swings toward +Y.
- Z is up, and the latch bolt centerline is at Z = 0.
- Positions along the arc are given as `s`: the arc length from the closed bolt, measured on radius `r_in`.

## Measured values

These are all in the `P` dataclass in `cat_door_latch.py`.

| Value | Meaning |
|---|---|
| Door: 28", 35 mm thick | |
| `pin_offset` 17.1 | The pivot sits 17.1 mm out from the door's room-side face. |
| Pivot to frame face: 15.9 | Hinge-side check. It lands on the model's jamb edge, `jamb_edge_y = -15.9`. |
| `latch_gap` 5.0 | Door latch edge to strike face. Calibrated from an installed test plate, not measured directly. |
| Strike recess: 33.2 x 57.4, about 1 mm deep | R5 corners on the stop side. |
| Latch hole: 20 x 26 | Its edge is 10 mm from the recess's room-side edge. |
| Wood screws: 41 mm apart | 19.33 mm from the recess's room-side edge. |
| `recess_to_casing_face` 15.7 | Recess room-side edge to the **front face of the trim**, not to the jamb edge (see lessons). |
| Trim: 17 mm deep | 5 mm reveal back from the strike face. |
| Latch bolt: 12.7 mm throw | The first 6.7 mm is square and the last 6 mm is beveled. Bevel faces the stop side. |

The user is not fluent in door terminology. "Outside edge" means the room side, and "door frame" means the jamb. When a measurement is ambiguous, confirm it with a drawn diagram (matplotlib PNG), not ASCII art.

## How the geometry works

### Plate front: `r_in`

- `r_in` is the radius of the door's farthest corner (stop side, latch edge) plus `swing_clear` (1.0).
- The plate's front and the arm's door-side face both lie on that arc.
- The door clears them by 1.34 mm when closed and by exactly 1.00 mm through the rest of the swing.
- That corner passes over every point of the plate. So the only way to make the plate thicker is to reduce `swing_clear`.

### Plate back

- The back is the flat plane `x = strike_x`, so the plate prints face-down.
- Its thickness follows from the arc and varies along it: about 2.9 mm at the latch and about 5 mm at the tail.
- There is no recess pad and no lip.

### Joint

- The arm root fills the 5 mm reveal and runs alongside the 17 mm of trim, 0.2 mm off the trim (`reveal_clear`).
- The root's end stops 1.5 mm short of the jamb edge (`root_gap`). Bearing on the jamb edge pushed the arm into the door's swing.
- A 1.5 mm corner fillet (`paint_fillet_r`) clears the painted inside corner.

### Bolts

- Bolt rows are placed by plate thickness, not by a fixed distance. `nut_floor` is 1.5 mm of plate behind the nearest nut, which needs a 4.0 mm plate.
- That puts the rows about 50 mm past the trim face, at 4.0 and 5.0 mm of plate.
- The screw length sets the counterbore depth in the arm, so each tip stops 0.3 mm short of the door-side face.

### Arm tip

- The tip has a 20 mm long, 9 mm deep lead-in ramp and flares outward to keep a 2 mm wall.
- The bolt's **bevel** therefore meets the tip first when the door closes from wide open, not its square face.

## Checks in `check()`

- The door swings from 0 to 40° with the bolt retracted, checked against both parts.
- The door is closed with the bolt out, checked against the plate.
- The door is held at the slot with the bolt in it.
- Both parts are checked against the jamb and against the casing.
- During development, also check that each part is a single solid and that the plate and arm don't overlap. Check `distance_to` gaps too, since an overlap of 0 can still mean the parts are touching.
- **Missing check:** the swing with the bolt extended, which is how the door actually closes. Contact along that sweep must land on the bevel (more than 6.7 mm past the door edge).

## Lessons learned (real installs)

1. **Hinge pivot.** The first prints assumed the pivot was about 3 mm off the door face, and the plate rubbed more the farther the door swung. Measuring the true rotation axis (17.1 mm) fixed it. Getting the pivot wrong shows up as rubbing that grows with the swing.
2. **Jamb edge was off by 17 mm.** The 15.7 mm measurement was taken to the trim's front face, but the model used it as the distance to the jamb edge. The arm root stopped 16.5 mm short of the frame. The pivot-to-frame measurement (15.9) cross-checks it, so keep both consistent.
3. **Closing jam.** The bolt's 6.7 mm square face hit the arm tip because the old ramp was only 4 mm deep. The swing check had run with the bolt retracted, which hid it.
4. **Arm flex.** An unsupported arm root lets the screws pull the arm into the door's path. The root has to bear on the trim. Clamping it hard against the jamb edge also bent the arm, hence the 1.5 mm `root_gap`.
5. **Nuts.** The user's M3 nuts are 2.4 mm. That is too thick for a pocket where the plate is under about 3 mm, which is why the bolts moved out to where the plate is thicker. Thin jam nuts (1.8 mm) would allow the bolts closer. A self-tapping version was tried and rejected as too weak. Heat-set inserts (3 mm long, 4.0 to 4.2 mm hole) would fit at the current bolt positions with a reprint of the plate only.
6. **Removed experiments.**
   - Arched or rounded slot tops: rejected, so the slot is plain rectangular.
   - Door edge bevel: reverted; the model uses a square door edge.
   - Slot 1: removed at the user's request.
   - Flat-head M3 screws: the user only has socket heads.
7. **Printing.** The arm lifted off its brim. Fix with brim-object gap 0 (see README).

## Open items

- Install and test the latest arm (tip ramp, 1.5 mm `root_gap`). The plate is unchanged since the nut version.
- If the door clears with margin, consider lowering `swing_clear` (0.5 mm would add 0.5 mm of plate thickness everywhere).
- Consider building mouse ears into the arm STL if brim-object gap 0 is not enough.
- Consider adding the bolt-extended closing sweep to `check()`.
