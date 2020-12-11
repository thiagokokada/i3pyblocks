{ config
, lib
, stdenv
, makeWrapper
, python3Packages
, extraLibs ? []
}:

python3Packages.buildPythonApplication rec {
  pname = "i3pyblocks";
  version = "master";

  src = builtins.fetchGit {
    url = "https://github.com/thiagokokada/i3pyblocks";
    ref = "master";
  };

  propagatedBuildInputs = extraLibs;

  checkInputs = with python3Packages; [
    asynctest
    mock
    pytest
    pytest-aiohttp
    pytest-asyncio
  ];

  checkPhase = ''
    pytest -c /dev/null
  '';

  meta = with stdenv.lib; {
    homepage = "https://github.com/thiagokokada/i3pyblocks";
    description = "A replacement for i3status, written in Python using asyncio.";
    license = licenses.mit;
    platforms = platforms.linux;
    maintainers = [ maintainers.thiagokokada ];
  };
}
