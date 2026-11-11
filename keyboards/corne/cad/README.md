# Corne LP case

Two-piece PETG wrap case for the Corne LP (corne-chocolate v3 / Helidox), nice!nano, left OLED, right PIM447.

![pair](renders/pair.jpg)
![trackball section](renders/right_section.jpg)

- `shell`: deck, walls and controller hump in one piece. The switches are soldered, so the deck is a cover with 15.8 mm holes rather than a switch plate. Take the keycaps off, then slide the PCB with its switches in from below; the cavity runs straight down and clears the switch housings that overhang the PCB edge. The hump covers the nice!nano, OLED, reset switch and TRRS jack (no opening for the jack)
- `floor`: drops in from below, so the only seam is on the bottom; has the MagSafe ring recess and battery fences
- 5 × M2×12 countersunk screws go up through the floor and PCB and thread straight into 1.8 mm pilot holes in bosses under the deck, which clamps shell, PCB and floor together. Lay the PCB into the upturned shell, then screw the floor on; go gently, it is ~3 mm of thread in PETG. Heads sit 2 mm up in wells in the floor
- PIM447 (right hump): the board sits in a 1 mm locating recess under the hump roof and is held by 4 × M2×4 self-tappers through its mounting holes; the trackball module pokes through the roof. The hump bulges ~1.2 mm past the case edge because the board (22 mm) is wider than the controller column. Solder wires to it (no pin header: the nice!nano is 3.5 mm below the board) and run them to the OLED header holes. Trim the right nice!nano's header pins to under 6 mm above the PCB so they clear the board and its screw heads
- No power switch: use `&soft_off`, and press reset to wake. `reset_pin` is a loose printed pin in the hump's reset hole: it rests on the switch with its top 0.3 mm under the surface, and a flange stops it falling out. Print one per half, standing on the flange. Its length assumes a 4.3 mm tall switch (`reset_sw`)

Heights: 14.6 mm at the keys, 23.5 mm at the hump. The PCB top sits 11.1 mm above the desk; the 6 mm battery (EEMB 603449) under the hotswap sockets sets this.

## Build

```sh
nix shell nixpkgs#uv -c uv run --python 3.12 --with manifold3d --with shapely --with numpy case.py   # -> models/*.stl
/Applications/Blender.app/Contents/MacOS/Blender -b -P render.py                                       # -> renders/*.jpg
```

Dimensions live in `P` at the top of `case.py`; the build asserts that the PCB with everything soldered on slides in from below. `pcb.json` holds the PCB outline and footprint positions from [foostan/crkbd v3-final](https://github.com/foostan/crkbd/blob/v3-final/corne-chocolate/pcb/corne-chocolate.kicad_pcb).

## Print

PETG, 0.2 mm layers. Print the floor flat. Print the shell upright (open side down) with tree supports from the build plate under the deck and hump roof; the bottom edge is a 45° chamfer so it needs none there. Use a 0.2–0.25 mm support top gap, since PETG fuses to tight supports.

`models/slice.3mf` is the Bambu Studio project; reload the STLs from disk after a rebuild.

Estimated, check before printing: nice!nano height on the stock headers (2.5 mm spacer; the USB-C opening is centred on it), OLED stack height, PIM447 module height, reset switch height, keycap skirt depth (the deck top is 1.5 mm below the switch housing top).
