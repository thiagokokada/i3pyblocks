import importlib.resources as pkg_resources

__version__ = pkg_resources.read_text(__package__, "version").strip()
