# i3pyblocks overlay for Nixpkgs

## Usage of the overlay

### Latest master each rebuild

One way, and probably the most convenient way to pull in this overlay is by
just fetching the tarball of latest master on rebuild.

This is not reproducible, but always ensure that you're running the latest
commit from i3pyblocks. Just add the following to your
`/etc/nixos/configuration.nix` file:

```nix
{
  # ...
  nixpkgs.overlays = [
    (import (builtins.fetchTarball {
      url = https://github.com/thiagokokada/i3pyblocks/archive/nix-overlay.tar.gz;
    }))
  ];
  environment.systemPackages = with pkgs; [
    i3pyblocks
  ];
  # ...
}
```

## Testing local

You can test without installing by using the included `shell.nix`, just run:

```sh
nix-shell
```

With that you will have a shell with your built derivation.

Also, using `nix-shell --pure` allows you to test just your derivation without
your system packages, making it easier to debug issues.
