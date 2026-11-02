{
  description = "ZMK firmware for my keyboards";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

    zmk-nix = {
      url = "github:lilyinstarlight/zmk-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, zmk-nix }: let
    forAllSystems = nixpkgs.lib.genAttrs (nixpkgs.lib.attrNames zmk-nix.packages);
  in {
    packages = forAllSystems (system: let
      inherit (zmk-nix.legacyPackages.${system}) buildKeyboard buildSplitKeyboard fetchZephyrDeps;

      src = nixpkgs.lib.sourceFilesBySuffices self [ ".conf" ".keymap" ".yml" ];

      # Update whenever config/west.yml changes; the build prints the new hash on a mismatch.
      zephyrDepsHash = "sha256-hlSPr62unE/JL1WY4AUFngCXbKjluJ7ZNi38eOV1GmQ=";

      # Shared so each keyboard doesn't download its own copy.
      westDeps = fetchZephyrDeps {
        inherit src;
        name = "zmk-west-deps";
        westRoot = "config";
        hash = zephyrDepsHash;
      };

      common = {
        inherit src westDeps zephyrDepsHash;
        board = "nice_nano//zmk";
      };

      # Lily58 and Lily58 Slim share a shield name, so each keyboard's
      # files are copied into the ZMK config directory at build time.
      splitKeyboard = name: shield: args: buildSplitKeyboard (common // {
        inherit name;
        shield = "${shield}_%PART%";
        preConfigure = "cp keyboards/${name}/* config/";
      } // args);
    in rec {
      default = corne;

      corne = splitKeyboard "corne" "corne" { enableZmkStudio = true; };
      lily58 = splitKeyboard "lily58" "lily58" { };
      lily58-slim = splitKeyboard "lily58-slim" "lily58" { };

      settings-reset = buildKeyboard (common // {
        name = "settings-reset";
        shield = "settings_reset";
      });
    });
  };
}
