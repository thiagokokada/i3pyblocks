import importlib.resources as pkg_resources
import logging

__version__ = pkg_resources.read_text(__package__, "version").strip()

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

from i3pyblocks.core import Runner
