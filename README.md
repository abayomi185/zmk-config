# ZMK Config

## Local Build Commands

```bash
west build -d build/left -b nice_nano_v2 -- -DSHIELD=corne_left
west build -d build/right -b nice_nano_v2 -- -DSHIELD=corne_right
```

https://zmk.dev/docs/features/encoders

https://zmk.dev/docs/features/keymaps/#root-devicetree-node

https://github.com/zmkfirmware/zmk/issues/674

https://github.com/infused-kim/zmk-zephyr/commits/v2.5.0%2Bzmk-fixes%2Bkim-fixes

https://github.com/infused-kim/zmk/tree/my-changes/oled-ext-pwr
