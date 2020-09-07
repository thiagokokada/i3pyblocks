self: super:

let
  callPackage = super.lib.callPackageWith super;
in
{
  i3pyblocks = callPackage ./pkgs/i3pyblocks.nix {};
}
