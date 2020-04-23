with import <nixpkgs> {};

let src = fetchFromGitHub {
  owner = "nix-community";
  repo = "poetry2nix";
  # Commit hash for master as of 2020-04-21
  # `git ls-remote https://github.com/nix-community/poetry2nix.git master`
  rev = "8d7d705aa070ebc615cfc73215f840bac24fffb3";
  sha256 = "1y4s92q4xa88jz5im6pwz0r713rxhvglsgyddgkkrg8xrd9rrajn";
};
in

with import "${src.out}/overlay.nix" pkgs pkgs;

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
