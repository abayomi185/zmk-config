# Corne LP case

Two-piece PETG wrap case for the Corne LP (corne-chocolate v3 / Helidox), nice!nano, left OLED, right PIM447.

![pair](renders/pair.jpg)
![trackball section](renders/right_section.jpg)

- `shell`: deck (doubles as the switch plate), walls and controller hump in one piece
- `floor`: drops in from below, so the only seam is on the bottom; has the MagSafe ring recess and battery fences
- 5 × M2×12 screws go up through the floor and PCB into blind bosses under the deck; cover the heads with rubber feet
- PIM447 (right hump): the board sits in a 1 mm locating recess under the hump roof and is held by 4 × M2×4 self-tappers through its mounting holes; the trackball module pokes through the roof. The hump bulges ~2.3 mm past the case edge because the board (22 mm) is wider than the controller column. Wire it from below to the OLED header holes
- No power switch: use `&soft_off`, and press reset (hole in the hump) to wake

Heights: 14.6 mm at the keys, 23.1 mm at the hump. The PCB top sits 11.1 mm above the desk; the 6 mm battery (EEMB 603449) under the hotswap sockets sets this.

## Build

```sh
nix shell nixpkgs#uv -c uv run --python 3.12 --with manifold3d --with shapely --with numpy case.py   # -> models/*.stl
/Applications/Blender.app/Contents/MacOS/Blender -b -P render.py                                       # -> renders/*.jpg
```

Dimensions live in `P` at the top of `case.py`. `pcb.json` holds the PCB outline and footprint positions from [foostan/crkbd v3-final](https://github.com/foostan/crkbd/blob/v3-final/corne-chocolate/pcb/corne-chocolate.kicad_pcb).

## Print

PETG, 0.2 mm layers. Print the floor flat. Print the shell upright (open side down) with supports under the deck and hump roof; the bottom edge is a 45° chamfer so it needs none there.

Estimated, check before printing: nice!nano height on the stock headers (2.5 mm spacer), OLED stack height, PIM447 module height.
