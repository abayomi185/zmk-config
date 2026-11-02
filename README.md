# ZMK Config

## Local Build Commands

```bash
nix build .#firmware --out-link result        # result/zmk_left.uf2, result/zmk_right.uf2
nix build .#settings-reset --out-link reset   # reset/zmk.uf2
```

After changing `config/west.yml`, update `zephyrDepsHash` in `flake.nix` with the hash the build prints.

Without Nix:

```bash
west build -d build/left -b nice_nano//zmk -S studio-rpc-usb-uart -- -DSHIELD=corne_left -DCONFIG_ZMK_STUDIO=y
west build -d build/right -b nice_nano//zmk -- -DSHIELD=corne_right
```

https://zmk.dev/docs/features/encoders

https://zmk.dev/docs/features/keymaps/#root-devicetree-node

https://github.com/zmkfirmware/zmk/issues/674

https://github.com/infused-kim/zmk-zephyr/commits/v2.5.0%2Bzmk-fixes%2Bkim-fixes

https://github.com/infused-kim/zmk/tree/my-changes/oled-ext-pwr
