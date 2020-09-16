{ config
, lib
, pkgs
, stdenv
, makeWrapper
  # Use Python from system so we ensure that we are using the same glibc
, pythonPkg ? pkgs.python38
, extraFeatures ? [
    "dbus"
    "http"
    "i3ipc"
    "inotify"
    "ps"
    "pulse"
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
