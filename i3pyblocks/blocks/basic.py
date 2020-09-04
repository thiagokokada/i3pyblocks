from i3pyblocks import blocks


class TextBlock(blocks.Block):
    def __init__(self, full_text: str, block_name=None, **kwargs) -> None:
        super().__init__(block_name=block_name)
        super().update_state(full_text=full_text, **kwargs)

    async def start(self) -> None:
        self.push_update()
