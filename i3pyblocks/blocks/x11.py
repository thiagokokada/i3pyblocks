"""Blocks related to X11, based on `python-xlib`_.

Blocks dedicated to control some X11 features. For example, ``CaffeineBlock``
shows the state of DPMS and screensaver and allow you to toggle DPMS between
ON and OFF.

Since query ``python-xlib`` calls are blocking, we execute than in a
ThreadPoolExecutor to avoid locking up the i3pyblocks. Since most X11 calls
do not take much time, this event should be rare, but it is better to be safe
(and correct!) than sorry.

.. _python-xlib:
    https://github.com/python-xlib/python-xlib
"""
from Xlib import X, display
from Xlib.ext import dpms  # noqa: F401 (ensure that Xlib.ext.dpms is available)

from i3pyblocks import blocks


class CaffeineBlock(blocks.PollingSyncBlock):
    r"""Block that controls of X11 DPMS and screensaver.

    When turned on, this blocks disables both `DPMS`_ and screensaver,
    effectively, keeping your screen on. When it is turned off this block
    re-enables both `DPMS`_ and screensaver. This is very similar to
    `Caffeine`_ extension in Gnome, or `Amphetamine`_ on macOS.

    :param format_on: format string to shown when DPMS and screensaver is off.

    :param format_off: format string to shown when DPMS and screensaver is on.

    :param sleep: Sleep in seconds between each call to
        :meth:`~i3pyblocks.blocks.base.PollingBlock.run()`.

    :param \*\*kwargs: Extra arguments to be passed to
        :class:`~i3pyblocks.blocks.base.PollingBlock` class.

    .. _DPMS:
        https://en.wikipedia.org/wiki/VESA_Display_Power_Management_Signaling
    .. _Caffeine:
        https://extensions.gnome.org/extension/517/caffeine/
    .. _Amphetamine:
        https://apps.apple.com/us/app/amphetamine/id937984704
    """

    def __init__(
        self,
        format_on: str = "CAFFEINE ON",
        format_off: str = "CAFFEINE OFF",
        sleep: int = 3,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format_on = format_on
        self.format_off = format_off
        self.display = display.Display()

    def get_state(self) -> bool:
        info = self.display.dpms_info()
        return bool(int(info.state))

    def click_handler_sync(self, **_kwargs) -> None:
        state = self.get_state()

        if state:
            self.display.dpms_disable()
            self.display.set_screen_saver(
                allow_exposures=X.DefaultExposures,
                interval=0,
                prefer_blank=X.DefaultBlanking,
                timeout=0,
            )
        else:
            self.display.dpms_enable()
            self.display.set_screen_saver(
                allow_exposures=X.DefaultExposures,
                interval=-1,
                prefer_blank=X.DefaultBlanking,
                timeout=-1,
            )

        self.display.sync()
        self.run_sync()

    def run_sync(self) -> None:
        state = self.get_state()
        self.update(self.format_off if state else self.format_on)
