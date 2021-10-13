{
  description = "i3pyblocks";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    {
      lib = {
        parseVersion = with nixpkgs.lib; versionFile:
          (replaceStrings [ " " "\"" ] [ "" "" ]
            (last
              (splitString "="
                (fileContents versionFile))));
      };

      overlay = final: prev: {
        i3pyblocks = self.defaultPackage;
      };
    } // flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };

        inherit (nixpkgs) lib;
        inherit (pkgs) python3Packages;
      in
      {
        customPackage =
          { extraLibs ? with python3Packages; [
              aiohttp
              aionotify
              dbus-next
              i3ipc
              psutil
              pulsectl
              xlib
            ]
          }:
          python3Packages.buildPythonApplication rec {
            pname = "i3pyblocks";
            version = self.lib.parseVersion ./i3pyblocks/__version__.py;

            src = ./.;

            propagatedBuildInputs = extraLibs;

            checkInputs = with python3Packages; [
              asynctest
              mock
              pytest-aiohttp
              pytest-asyncio
              pytestCheckHook
            ];

            meta = with lib; {
              homepage = "https://github.com/thiagokokada/i3pyblocks";
              description = "A replacement for i3status, written in Python using asyncio.";
              license = licenses.mit;
              platforms = platforms.linux;
            };
          };

        defaultPackage = self.customPackage.${system} { };

        devShell = import ./shell.nix { inherit pkgs; };
      }
    );
}
