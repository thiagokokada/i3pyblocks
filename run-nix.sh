#!/bin/sh
cd $(dirname "${0}")
nix-shell --run "venv/bin/python3 run.py"
