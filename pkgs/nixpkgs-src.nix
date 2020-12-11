{ fakeSha256 }:

builtins.fetchTarball {
    url = "https://github.com/nixos/nixpkgs/tarball/53301ab31b7ff2ccb93934e3427f13a7d5aa9801";
    # Use fakeSha256 to generate a new sha256 when updating, i.e.:
    # sha256 = fakeSha256;
    sha256 = "017mh1f5lkxhq6zk63li6rcfi2i86gk069nyvvpm84dcn88qc7dg";
}
