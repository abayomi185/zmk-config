{
  description = "ZMK firmware for my Corne";

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
      inherit (zmk-nix.legacyPackages.${system}) buildKeyboard buildSplitKeyboard;

      common = {
        src = nixpkgs.lib.sourceFilesBySuffices self [ ".conf" ".keymap" ".yml" ];
        board = "nice_nano//zmk";

        # Update whenever config/west.yml changes; the build prints the new hash on a mismatch.
        zephyrDepsHash = "sha256-hlSPr62unE/JL1WY4AUFngCXbKjluJ7ZNi38eOV1GmQ=";
      };
    in rec {
      default = firmware;

      firmware = buildSplitKeyboard (common // {
        name = "corne";
        shield = "corne_%PART%";
        enableZmkStudio = true;
      });

      settings-reset = buildKeyboard (common // {
        name = "settings-reset";
        shield = "settings_reset";
      });
    });
  };
}
