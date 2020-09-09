{ stdenv, python3Packages, }:

python3Packages.buildPythonApplication rec {
  pname = "aionotify";
  version = "0.2.0";

  src = builtins.fetchGit {
    url = "https://github.com/rbarrois/aionotify";
    ref = "master";
    rev = "cc3dea411a15f1781c1c56b45fdf9ce583629db7";
  };

  checkInputs = with python3Packages; [
    asynctest
  ];

  meta = with stdenv.lib; {
    homepage = "https://github.com/rbarrois/i3paionotify";
    description = "Simple, asyncio-based inotify library for Python";
    license = licenses.bsd2;
    platforms = platforms.linux;
    maintainers = [ maintainers.thiagokokada ];
  };
}
