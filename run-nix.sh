#!/bin/sh
cd $(dirname "${0}")
nix-shell --run "poetry run python3 run.py"
