{ pkgs ? import <nixpkgs> { } }:

with pkgs;
let
  venvDir = "./venv";
  pythonEnv = python38Full;
in
mkShell {
  name = "i3pyblocks";
  buildInputs = [
    libpulseaudio
    pythonEnv
  ];
  LD_LIBRARY_PATH = "${libpulseaudio}/lib";

  shellHook = ''
    SOURCE_DATE_EPOCH=$(date +%s)

    echoerr() { echo "$@" 1>&2; }

    if [ -d "${venvDir}" ]; then
      echoerr "Skipping venv creation, '${venvDir}' already exists"
    else
      echoerr "Creating new venv environment in path: '${venvDir}'"
      ${pythonEnv.interpreter} -m venv "${venvDir}" 1>&2
    fi

    source "${venvDir}/bin/activate"

    make dev-install 1>&2
  '';
}
