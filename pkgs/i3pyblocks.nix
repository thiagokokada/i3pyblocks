{ lib
, python3Packages
, extraLibs ? with python3Packages; [
    aiohttp
    aionotify
    dbus-next
    i3ipc
    psutil
    pulsectl
    xlib
  ]
}:

python3Packages.buildPythonApplication rec {
  pname = "i3pyblocks";
  version = "master";

  src = builtins.fetchGit {
    url = "https://github.com/thiagokokada/${pname}";
    ref = version;
  };

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
    maintainers = [ maintainers.thiagokokada ];
  };
}
