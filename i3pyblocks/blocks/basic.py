from i3pyblocks import blocks


class TextBlock(blocks.Block):
    def __init__(self, full_text: str, **kwargs) -> None:
        super().__init__(block_name=kwargs.pop("block_name", None))
        super().update_state(full_text=full_text, **kwargs)

    async def start(self) -> None:
        self.push_update()
