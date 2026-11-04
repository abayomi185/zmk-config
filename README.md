# ZMK Config

## Keyboards

Each keyboard has its own folder in `keyboards/`. Lily58 and Lily58 Slim are separate keyboards that share the `lily58` shield.

## Building

```bash
nix build .#corne --out-link result          # result/zmk_left.uf2, result/zmk_right.uf2
nix build .#lily58 --out-link result
nix build .#lily58-slim --out-link result
nix build .#settings-reset --out-link reset  # reset/zmk.uf2
```

After changing `config/west.yml`, update `zephyrDepsHash` in `flake.nix` with the hash the build prints.

GitHub Actions builds every keyboard on push and pull request. To build one, run the workflow manually and pick a keyboard (default: all).

https://zmk.dev/docs/features/encoders

https://zmk.dev/docs/features/keymaps/#root-devicetree-node

https://github.com/zmkfirmware/zmk/issues/674

https://github.com/infused-kim/zmk-zephyr/commits/v2.5.0%2Bzmk-fixes%2Bkim-fixes

https://github.com/infused-kim/zmk/tree/my-changes/oled-ext-pwr
