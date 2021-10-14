{ pkgs ? import <nixpkgs> { }
, extraLibs ? with pkgs.python3Packages; [
    aiohttp
    aionotify
    dbus-next
    i3ipc
    psutil
    pulsectl
    xlib
  ]
}:

with pkgs;
with pkgs.lib;

python3Packages.buildPythonApplication rec {
  pname = "i3pyblocks";
  version = (lib.fileContents ./i3pyblocks/version);

  src = ./.;

  propagatedBuildInputs = extraLibs;

  checkInputs = with python3Packages; [
    asynctest
    mock
    pytest-aiohttp
    pytest-asyncio
    pytestCheckHook
  ];

  meta = with lib; {
    homepage = "https://github.com/thiagokokada/i3pyblocks";
    description = "A replacement for i3status, written in Python using asyncio.";
    license = licenses.mit;
    platforms = platforms.linux;
  };
}
