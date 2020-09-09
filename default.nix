self: super:

let
  callPackage = super.lib.callPackageWith super;
in
rec {
  # Define some dependencies that are not package yet in nixpkgs
  _ = {
    aionotify = callPackage ./pkgs/aionotify.nix {};
  };

  i3pyblocks = callPackage ./pkgs/i3pyblocks.nix {
    extraLibs = with super.python3Packages; [
      _.aionotify
      aiohttp
      i3ipc
      psutil
      pulsectl
    ];
  };
}
