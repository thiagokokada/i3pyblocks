with import <nixpkgs> {};

let pythonEnv = poetry2nix.mkPoetryEnv {
  projectDir = ./.;
};
in
mkShell {
  name = "i3pyblocks";
  buildInputs = [
    libffi
    libpulseaudio
    python37Packages.poetry
    pythonEnv
  ];
  LD_LIBRARY_PATH="${libpulseaudio}/lib";
}
