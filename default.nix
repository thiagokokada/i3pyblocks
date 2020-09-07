self: super:

let
  callPackage = super.lib.callPackageWith super;
in
{
  i3pyblocks = callPackage ./nix/i3pyblocks.nix {};
}
