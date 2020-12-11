self: super:

let
  unstable = import (import ./pkgs/nixpkgs-src.nix {
    fakeSha256 = unstable.stdenv.lib.fakeSha256;
  }) {
    config = {};
    overlays = [];
  };
in
{
  i3pyblocks = unstable.callPackage ./pkgs/i3pyblocks.nix {
    python3Packages = unstable.python3Packages;
    extraLibs = with unstable.python3Packages; [
      aiohttp
      aionotify
      dbus-next
      i3ipc
      psutil
      pulsectl
      xlib
    ];
  };
}
