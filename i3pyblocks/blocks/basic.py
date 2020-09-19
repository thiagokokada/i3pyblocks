"""Blocks that does not have any extra dependency except i3pyblock itself."""

from i3pyblocks import blocks


class TextBlock(blocks.Block):
    r"""Block that shows arbitrary text in i3pyblocks.

    :param full_text:
        Text to be shown.

    :param \*\*kwargs: Arguments to be passed to
        :meth:`i3pyblocks.blocks.base.Block.update_state()` method.
    """

    def __init__(self, full_text: str, **kwargs) -> None:
        super().__init__(block_name=kwargs.pop("block_name", None))
        super().update_state(full_text=full_text, **kwargs)

    async def start(self) -> None:
        self.push_update()
