{ config
, lib
, pkgs
, stdenv
, makeWrapper
  # Use Python from system so we ensure that we are using the same glibc
, pythonPkg ? pkgs.python38
, extraLibs ? ''
    aiohttp
    aionotify
    dbus-next
    i3ipc
    psutil
    pulsectl
  ''
}:

let
  libs = with pkgs; [
    libpulseaudio
  ];
  mach-nix = import (
    builtins.fetchGit {
      url = "https://github.com/DavHau/mach-nix/";
      ref = "refs/tags/2.3.0";
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

  requirements = extraLibs;

  buildInputs = libs ++ [ makeWrapper ];

  makeWrapperArgs = [
    "--suffix"
    "LD_LIBRARY_PATH"
    ":"
    "${stdenv.lib.makeLibraryPath libs}"
  ];

  meta = with stdenv.lib; {
    homepage = "https://github.com/thiagokokada/i3pyblocks";
    description = "A replacement for i3status, written in Python using asyncio.";
    license = licenses.mit;
    platforms = platforms.linux;
    maintainers = [ maintainers.thiagokokada ];
  };

  python = pythonPkg;
}
