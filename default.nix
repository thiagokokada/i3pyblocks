with import <nixpkgs> {};

stdenv.mkDerivation rec {
  name = "i3pyblocks";

  buildInputs = [
    libpulseaudio
    python37Full
    python37Packages.poetry
  ];

  LD_LIBRARY_PATH="${libpulseaudio}/lib";
}
