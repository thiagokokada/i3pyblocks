with import <nixpkgs> {};

let pythonEnv = poetry2nix.mkPoetryEnv {
  projectDir = ./.;
};
in
mkShell {
  name = "i3pyblocks";
  nativeBuildInputs = [
    libffi
    libpulseaudio
    pythonEnv
  ];
  LD_LIBRARY_PATH="${libpulseaudio}/lib";
}
