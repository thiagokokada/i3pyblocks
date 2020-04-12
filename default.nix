with import <nixpkgs> {};

# TODO: Migrate to poetry2nix.mkPoetryEnv
stdenv.mkDerivation rec {
  name = "i3pyblocks";

  buildInputs = [
    libpulseaudio
    python37Full
    libffi
    # poetry is broken in NixOS 19.09
    # python37Packages.poetry
  ];

  LD_LIBRARY_PATH="${libpulseaudio}/lib";
}
