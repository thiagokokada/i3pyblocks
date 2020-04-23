#!/bin/sh
cd $(dirname "${0}")
nix-shell --run "./run.py"
