self: super:

let
  unstable = import (builtins.fetchTarball {
    url = "https://github.com/nixos/nixpkgs/tarball/257cbbcd3ab7bd96f5d24d50adc807de7c82e06d";
    # Use fakeSha256 to generate a new sha256 when updating, i.e.:
    # sha256 = super.stdenv.lib.fakeSha256;
    sha256 = "0g3n725kjk2fc9yn9rvdjwci4mrx58yrdgp3waby9ky3d5xhcaw4";
  }) {};
in
{
  i3pyblocks = unstable.callPackage ./pkgs/i3pyblocks.nix { };
}
