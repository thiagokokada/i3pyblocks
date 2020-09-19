{ config
, lib
, pkgs
, stdenv
, makeWrapper
  # Use Python from system so we ensure that we are using the same glibc
, pythonPkg ? pkgs.python38
, extraFeatures ? [
    "blocks.dbus"
    "blocks.http"
    "blocks.i3ipc"
    "blocks.inotify"
    "blocks.ps"
    "blocks.pulse"
    # "blocks.x11"
  ]
}:

let
  libs = with pkgs; [ libpulseaudio ];
  mach-nix = import (
    builtins.fetchGit {
      url = "https://github.com/DavHau/mach-nix/";
      rev = "7efb5de273cf0c7556fe2f318d2593b5e17d77c3";
      ref = "master";
    }
  );
in
mach-nix.buildPythonApplication rec {
  pname = "i3pyblocks";
  version = "master";

  src = builtins.fetchGit {
    url = "https://github.com/thiagokokada/i3pyblocks";
    ref = "master";
  };

  extras = extraFeatures ++ [ "test" ];

  buildInputs = libs ++ [ makeWrapper ];

  overrides_pre = [
    (
      pySelf: pySuper: {
        xlib = pySuper.xlib.overrideAttrs (
          oldAttrs: {
            src = builtins.fetchTarball "https://github.com/python-xlib/python-xlib/tarball/efc07c4132e48098a0e81ac577b22f63cd7356d9";
            pname = "python-xlib";
          }
        );
      }
    )
  ];

  providers.python-xlib = "nixpkgs";

  makeWrapperArgs =
    [ "--suffix" "LD_LIBRARY_PATH" ":" "${stdenv.lib.makeLibraryPath libs}" ];

  disable_checks = false;

  checkPhase = ''
    export LD_LIBRARY_PATH="${stdenv.lib.makeLibraryPath libs}"
    ${pythonPkg.interpreter} -m pytest
  '';

  meta = with stdenv.lib; {
    homepage = "https://github.com/thiagokokada/i3pyblocks";
    description = "A replacement for i3status, written in Python using asyncio.";
    license = licenses.mit;
    platforms = platforms.linux;
    maintainers = [ maintainers.thiagokokada ];
  };

  python = pythonPkg;
}
