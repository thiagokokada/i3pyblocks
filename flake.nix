{
  description = "i3pyblocks";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    {
      overlay = final: prev: {
        i3pyblocks = self.defaultPackage;
      };
    } // flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        # Use this to build a custom version of i3pyblocks by
        # overriding extraLibs param
        customPackage = import ./default.nix;

        defaultPackage = self.customPackage.${system} { inherit pkgs; };

        devShell = import ./shell.nix { inherit pkgs; };
      }
    );
}
