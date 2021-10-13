{
  description = "i3pyblocks";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        inherit (nixpkgs) lib;
        inherit (pkgs) python3Packages;
        parseVersion = with builtins; with lib; versionFile:
          (replaceStrings [" " "\""] ["" ""]
            (last
              (splitString "="
                (fileContents versionFile))));
      in
      {
        defaultPackage = python3Packages.buildPythonApplication rec {
          pname = "i3pyblocks";
          version = parseVersion ./i3pyblocks/__version__.py;

          src = ./.;

          propagatedBuildInputs = with python3Packages; [
            aiohttp
            aionotify
            dbus-next
            i3ipc
            psutil
            pulsectl
            xlib
          ];

          meta = with lib; {
            homepage = "https://github.com/thiagokokada/i3pyblocks";
            description = "A replacement for i3status, written in Python using asyncio.";
            license = licenses.mit;
            platforms = platforms.linux;
          };
        };

        overlay = final: prev: {
          i3pyblocks = self.defaultPackage;
        };

        devShell = import ./shell.nix { inherit pkgs; };
      }
    );
}
