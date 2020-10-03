import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

from i3pyblocks.core import Runner
