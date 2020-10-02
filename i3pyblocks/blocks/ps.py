"""Blocks related to process and system information, based on `psutil`_.

This is a collection of many Blocks based on ``psutil``, a cross-platform
library for retrieving information on running processes and system utilization
(CPU, memory, disks, network, sensors) in Python.

Blocks in this module show information about your running system, including
useful information i.e.: how many memory is in currently use
(``VirtualMemoryBlock``) or the current speed of the connected Ethernet/Wi-Fi
interface (``NetworkSpeedBlock``).

All Blocks in this module are based on ``PollingBlock`` since this kinda of
measurement only makes sense over time (i.e.: memory is always changing so we
can't just update when memory usage increase/decrease or we would use too much
resources for it).

.. _psutil:
    https://github.com/giampaolo/psutil
"""

import datetime
import re
import time
from pathlib import Path
from typing import Optional, Tuple, Union

import psutil
from psutil._common import bytes2human

from i3pyblocks import blocks, types
from i3pyblocks._internal import misc, models


class CpuPercentBlock(blocks.PollingBlock):
    r"""Block that shows the current CPU percentage.

    :param format: Format string to shown. Supports both ``{percent}`` and
        ``{icon}`` placeholders.

    :param colors: A mapping that represents the color that will be shown in
        each CPU interval. For example::

            {
                0: "000000",
                10: "#FF0000",
                50: "#FFFFFF",
            }

        When the CPU % is between [0, 10) the color is set to "000000", from
        [10, 50) is set to "FF0000" and from 50 and beyond it is "#FFFFFF".

    :param icons: Similar to ``colors``, but for icons. Can be used to create a
        graphic representation of the CPU %. Only displayed when ``format``
        includes ``{icon}`` placeholder.

    :param sleep: Sleep in seconds between each call to
        :meth:`~i3pyblocks.blocks.base.PollingBlock.run()`.

    :param \*\*kwargs: Extra arguments to be passed to
        :class:`~i3pyblocks.blocks.base.PollingBlock` class.
    """

    def __init__(
        self,
        format: str = "C: {percent}%",
        colors: models.Threshold = {
            0: types.Color.NEUTRAL,
            75: types.Color.WARN,
            90: types.Color.URGENT,
        },
        icons: models.Threshold = {
            0.0: "▁",
            12.5: "▂",
            25.0: "▃",
            37.5: "▄",
            50.0: "▅",
            62.5: "▆",
            75.0: "▇",
            87.5: "█",
        },
        sleep: int = 5,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.colors = colors
        self.icons = icons

    async def run(self) -> None:
        percent = psutil.cpu_percent(interval=None)

        color = misc.calculate_threshold(self.colors, percent)
        icon = misc.calculate_threshold(self.icons, percent)

        self.update(
            self.ex_format(
                self.format,
                percent=percent,
                icon=icon,
            ),
            color=color,
        )


class DiskUsageBlock(blocks.PollingBlock):
    r"""Block that shows the current disk usage for path.

    :param path: Path to the disk to shown.

    :param format: Format string to shown. Supports the following placeholders:

        - ``{path}``: Disk path, for example: ``/mnt/backup``
        - ``{short_path}``: Disk path, but only show the first letter of each
          directory, for example: ``/m/b``
        - ``{total}``: Disk total size
        - ``{used}``: Disk used size
        - ``{free}``: Disk free size
        - ``{percent}``: Disk usage in percentage
        - ``{icon}``: Show disk usage percentage in icon representation

    :param colors: A mapping that represents the color that will be shown in
        each disk usage in percentage interval. For example::

            {
                0: "000000",
                10: "#FF0000",
                50: "#FFFFFF",
            }

        When the disk % is between [0, 10) the color is set to "000000", from
        [10, 50) is set to "FF0000" and from 50 and beyond it is "#FFFFFF".

    :param icons: Similar to ``colors``, but for icons. Can be used to create a
        graphic representation of the disk %. Only displayed when ``format``
        includes ``{icon}`` placeholder.

    :param divisor: Divisor used for all size reportings for this Block. For
        example, using ``1024 ** 1024`` here makes all sizes return in MiB.

    :param sleep: Sleep in seconds between each call to
        :meth:`~i3pyblocks.blocks.base.PollingBlock.run()`.

    :param \*\*kwargs: Extra arguments to be passed to
        :class:`~i3pyblocks.blocks.base.PollingBlock` class.
    """

    def __init__(
        self,
        path: Union[Path, str] = "/",
        format: str = "{path}: {free:.1f}GiB",
        colors: models.Threshold = {
            0: types.Color.NEUTRAL,
            75: types.Color.WARN,
            90: types.Color.URGENT,
        },
        icons: models.Threshold = {
            0.0: "▁",
            12.5: "▂",
            25.0: "▃",
            37.5: "▄",
            50.0: "▅",
            62.5: "▆",
            75.0: "▇",
            87.5: "█",
        },
        divisor: int = types.IECUnit.GiB,
        sleep: int = 5,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.colors = colors
        self.icons = icons
        self.divisor = divisor
        self.path = Path(path)
        self.short_path = self._get_short_path()

    def _convert(self, dividend: float) -> float:
        return dividend / self.divisor

    def _get_short_path(self) -> str:
        return "/" + "/".join(x[0] for x in str(self.path).split("/") if x)

    async def run(self) -> None:
        disk = psutil.disk_usage(str(self.path))

        color = misc.calculate_threshold(self.colors, disk.percent)
        icon = misc.calculate_threshold(self.icons, disk.percent)

        self.update(
            self.ex_format(
                self.format,
                path=self.path,
                short_path=self.short_path,
                total=self._convert(disk.total),
                used=self._convert(disk.used),
                free=self._convert(disk.free),
                percent=disk.percent,
                icon=icon,
            ),
            color=color,
        )


class LoadAvgBlock(blocks.PollingBlock):
    r"""Block that shows the current load average, in the last 1, 5 or 15 minutes.

    :param format: Format string to shown. Supports the ``{load1}``, ``{load5}``
        and ``{load15}`` placeholders.

    :param colors: A mapping that represents the color that will be shown in each
        load1 interval. For example::

            {
                0: "000000",
                2: "#FF0000",
                4: "#FFFFFF",
            }

        When the load1 is between [0, 2) the color is set to "000000", from
        [2, 4) is set to "FF0000" and from 4 and beyond it is "#FFFFFF".

    :param sleep: Sleep in seconds between each call to
        :meth:`~i3pyblocks.blocks.base.PollingBlock.run()`.

    :param \*\*kwargs: Extra arguments to be passed to
        :class:`~i3pyblocks.blocks.base.PollingBlock` class.
    """

    def __init__(
        self,
        format: str = "L: {load1}",
        colors: models.Threshold = {
            0: types.Color.NEUTRAL,
            2: types.Color.WARN,
            4: types.Color.URGENT,
        },
        sleep: int = 5,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.colors = colors

    async def run(self) -> None:
        load1, load5, load15 = psutil.getloadavg()

        color = misc.calculate_threshold(self.colors, load1)

        self.update(
            self.ex_format(self.format, load1=load1, load5=load5, load15=load15),
            color=color,
        )


class NetworkSpeedBlock(blocks.PollingBlock):
    r"""Block that shows the current network speed for the connect interface.

    :param format_up: Format string to shown when there is at least one
        connected interface. Supports the following placeholders:

        - ``{interface}``: Interface name, for example: ``eno1``
        - ``{upload}``: Upload speed
        - ``{download}``: Download speed

        Since upload/download speeds varies greatly during usage, this module
        automatically finds the most compact speed representation. So instead
        of showing ``1500K`` it will show ``1.5M``, for example.

    :param format_down: Format string to shown when there is no connected
        interface.

    :param colors: A mapping that represents the color that will be shown in
        each load1 interval. For example::

            {
                0: "000000",
                2 * types.IECUnit.MIB: "#FF0000",
                4 * types.IECUnit.MIB: "#FFFFFF",
            }

        When the network speed is between [0, 2) MiB the color is set to
        "000000", from [2, 4) is set to "FF0000" and from 4 and beyond it is
        "#FFFFFF".

    :param interface_regex: Regex for which interfaces to use. By default it
         already includes the most common ones and excludes things like ``lo``
         (loopback interface).

    :param sleep: Sleep in seconds between each call to
        :meth:`~i3pyblocks.blocks.base.PollingBlock.run()`.

    :param \*\*kwargs: Extra arguments to be passed to
        :class:`~i3pyblocks.blocks.base.PollingBlock` class.
    """

    def __init__(
        self,
        format_up: str = "{interface}:  U {upload} D {download}",
        format_down: str = "No network",
        colors: models.Threshold = {
            0: types.Color.NEUTRAL,
            2 * types.IECUnit.MiB: types.Color.WARN,
            5 * types.IECUnit.MiB: types.Color.URGENT,
        },
        interface_regex: str = r"en*|eth*|ppp*|sl*|wl*|ww*",
        sleep: int = 3,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format_up = format_up
        self.format_down = format_down
        self.colors = colors
        self.interface_regex = re.compile(interface_regex)
        self.interface = self._find_interface()
        self.previous = psutil.net_io_counters(pernic=True)
        self.previous_time = time.time()

    def _find_interface(
        self,
        previous_interface: Optional[str] = None,
    ) -> Optional[str]:
        interfaces_stats = psutil.net_if_stats()

        # Give preference to the current interface if more than one interface
        # match the rules
        previous_stats = interfaces_stats.get(previous_interface)
        if previous_stats and previous_stats.isup:
            return previous_interface

        for interface, stats in interfaces_stats.items():
            if stats.isup and self.interface_regex.match(interface):
                return interface

        return None

    def _calculate_speed(
        self, previous, previous_time, now, now_time
    ) -> Tuple[float, float]:
        upload = (now.bytes_sent - previous.bytes_sent) / (now_time - previous_time)
        download = (now.bytes_recv - previous.bytes_recv) / (now_time - previous_time)

        return upload, download

    async def run(self) -> None:
        self.interface = self._find_interface(self.interface)

        if not self.interface:
            self.update(self.format_down, color=types.Color.URGENT)
            return

        now = psutil.net_io_counters(pernic=True)
        now_time = time.time()

        if self.interface in now.keys():
            upload, download = self._calculate_speed(
                self.previous[self.interface],
                self.previous_time,
                now[self.interface],
                now_time,
            )
        else:
            upload, download = 0, 0

        color = misc.calculate_threshold(self.colors, max(upload, download))

        self.update(
            self.ex_format(
                self.format_up,
                upload=bytes2human(upload),
                download=bytes2human(download),
                interface=self.interface,
            ),
            color=color,
        )

        self.previous = now
        self.previous_time = now_time


class SensorsBatteryBlock(blocks.PollingBlock):
    r"""Block that shows battery information.

    :param format_plugged: Format string to shown when the battery is plugged
        (charging). support the following placeholders:

        - ``{percent}``: battery capacity in percentage
        - ``{remaining_time}``: battery remaining time
        - ``{icon}``: show battery capacity percentage in icon representation

    :param format_unplugged: Format string to shown when the battery is unplugged
        (discharging). Supports the same placeholders as ``format_unplugged``.

    :param format_unknown: Format string to shown when the battery is an unknown
        state. Supports the same placeholders as ``format_unplugged``.

    :param format_no_battery: Format string to shown when no battery is detected.

    :param colors: A mapping that represents the color that will be shown in each
        battery percentage interval. For example::

            {
                0: "000000",
                10: "#FF0000",
                25: "#FFFFFF",
            }

        When the battery percentage is between [0, 10) % the color is set to
        "000000", from [10, 25) is set to "FF0000" and from 25 and beyond it is
        "#FFFFFF".

    :param icons: Similar to ``colors``, but for icons. Can be used to create a
        graphic representation of the battery %. Only displayed when ``format``
        includes ``{icon}`` placeholder.

    :param sleep: Sleep in seconds between each call to
        :meth:`~i3pyblocks.blocks.base.PollingBlock.run()`.

    :param \*\*kwargs: Extra arguments to be passed to
        :class:`~i3pyblocks.blocks.base.PollingBlock` class.
    """

    def __init__(
        self,
        format_plugged: str = "B: PLUGGED {percent:.0f}%",
        format_unplugged: str = "B: {icon} {percent:.0f}% {remaining_time}",
        format_unknown: str = "B: {icon} {percent:.0f}%",
        format_no_battery: str = "No battery",
        colors: models.Threshold = {
            0: types.Color.URGENT,
            10: types.Color.WARN,
            25: types.Color.NEUTRAL,
        },
        icons: models.Threshold = {
            0.0: "▁",
            12.5: "▂",
            25.0: "▃",
            37.5: "▄",
            50.0: "▅",
            62.5: "▆",
            75.0: "▇",
            87.5: "█",
        },
        sleep: int = 5,
        **kwargs,
    ):
        super().__init__(sleep=sleep, **kwargs)
        self.format_plugged = format_plugged
        self.format_unplugged = format_unplugged
        self.format_unknown = format_unknown
        self.format_no_battery = format_no_battery
        self.colors = colors
        self.icons = icons

    async def run(self):
        battery = psutil.sensors_battery()

        # This state maybe temporary trigged by a battery connection/disconnection
        if not battery:
            self.update(self.format_no_battery, color=types.Color.URGENT)
            return

        color = misc.calculate_threshold(self.colors, battery.percent)
        icon = misc.calculate_threshold(self.icons, battery.percent)

        if battery.power_plugged or battery.secsleft == psutil.POWER_TIME_UNLIMITED:
            self.format = self.format_plugged
        else:
            if battery.secsleft == psutil.POWER_TIME_UNKNOWN:
                self.format = self.format_unknown
            else:
                self.format = self.format_unplugged

        self.update(
            self.ex_format(
                self.format,
                percent=battery.percent,
                remaining_time=(datetime.timedelta(seconds=battery.secsleft)),
                icon=icon,
            ),
            color=color,
        )


class SensorsTemperaturesBlock(blocks.PollingBlock):
    r"""Block that shows sensor temperature information.

    :param format: Format string to shown. Support the following placeholders:

        - ``{label}``: Label of the sensor. Architecture specific
        - ``{current}``: Current temperature reported by sensor
        - ``{high}``: Highest temperature reported by sensor
        - ``{critical}``: Critical temperature reported by sensor
        - ``{icon}``: Show sensor temperature in icon representation

    :param colors: A mapping that represents the color that will be shown in each
        temperature interval. For example::

            {
                0: "000000",
                50: "#FF0000",
                80: "#FFFFFF",
            }

        When the sensor temperature is between [0, 50) % the color is set to
        "000000", from [50, 80) is set to "FF0000" and from 80 and beyond it is
        "#FFFFFF".

    :param icons: Similar to ``colors``, but for icons. Can be used to create a
        graphic representation of the temperature. Only displayed when ``format``
        includes ``{icon}`` placeholder.

    :param fahrenheit: Show temperature in in Fahrenheit instead of Celsius.

    :param sensor_regex: Regex to be used by search the sensor name. If it
        matches more than one, the first one will be picked.

    :param sensor_index: Sensor index that should be used. Most sensors have
        more than one sensor (for example, one for each CPU), so this setting
        allow you to pick each one you want.

    :param sleep: Sleep in seconds between each call to
        :meth:`~i3pyblocks.blocks.base.PollingBlock.run()`.

    :param \*\*kwargs: Extra arguments to be passed to
        :class:`~i3pyblocks.blocks.base.PollingBlock` class.
    """

    def __init__(
        self,
        format: str = "T: {current:.0f}°C",
        format_no_sensor: str = "No sensor",
        colors: models.Threshold = {
            0: types.Color.NEUTRAL,
            60: types.Color.WARN,
            85: types.Color.URGENT,
        },
        icons: models.Threshold = {
            0.0: "▁",
            12.5: "▂",
            25.0: "▃",
            37.5: "▄",
            50.0: "▅",
            62.5: "▆",
            75.0: "▇",
            87.5: "█",
        },
        fahrenheit: bool = False,
        sensor_regex: str = r".*",
        sensor_index: int = 0,
        sleep: int = 5,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.format_no_sensor = format_no_sensor
        self.colors = colors
        self.icons = icons
        self.fahrenheit = fahrenheit
        self.sensor_index = sensor_index

        sensors = psutil.sensors_temperatures().keys()
        self.sensor = next((s for s in sensors if re.search(sensor_regex, s)), None)

    async def run(self) -> None:
        temperatures = psutil.sensors_temperatures(self.fahrenheit).get(self.sensor, [])
        temperature = (
            temperatures[self.sensor_index]
            if self.sensor_index < len(temperatures)
            else None
        )

        if not temperature:
            self.update(self.format_no_sensor, color=types.Color.URGENT)
            return

        color = misc.calculate_threshold(self.colors, temperature.current)
        icon = misc.calculate_threshold(self.icons, temperature.current)

        self.update(
            self.ex_format(
                self.format,
                label=temperature.label,
                current=temperature.current,
                high=temperature.high,
                critical=temperature.critical,
                icon=icon,
            ),
            color=color,
        )


class VirtualMemoryBlock(blocks.PollingBlock):
    r"""Block that shows virtual memory information.

    :param format: Format string to shown. Support the following placeholders:

        - ``{total}``: Total installed memory
        - ``{available}``: Available memory
        - ``{used}``: Used memory
        - ``{free}``: Free memory
        - ``{percent}``: Percent used memory
        - ``{icon}``: Show memory percent in icon representation

    :param colors: A mapping that represents the color that will be shown in each
        used memory percentage. For example::

            {
                0: "000000",
                50: "#FF0000",
                80: "#FFFFFF",
            }

        When the used memory % is between [0, 50) % the color is set to
        "000000", from [50, 80) is set to "FF0000" and from 80 and beyond it is
        "#FFFFFF".

    :param divisor: Divisor used for all size reportings for this Block. For
        example, using ``1024 ** 1024`` here makes all sizes return in MiB.

    :param icons: Similar to ``colors``, but for icons. Can be used to create a
        graphic representation of the used memory. Only displayed when ``format``
        includes ``{icon}`` placeholder.

    :param sleep: Sleep in seconds between each call to
        :meth:`~i3pyblocks.blocks.base.PollingBlock.run()`.

    :param \*\*kwargs: Extra arguments to be passed to
        :class:`~i3pyblocks.blocks.base.PollingBlock` class.
    """

    def __init__(
        self,
        format: str = "M: {available:.1f}GiB",
        colors: models.Threshold = {
            0: types.Color.NEUTRAL,
            75: types.Color.WARN,
            90: types.Color.URGENT,
        },
        icons: models.Threshold = {
            0.0: "▁",
            12.5: "▂",
            25.0: "▃",
            37.5: "▄",
            50.0: "▅",
            62.5: "▆",
            75.0: "▇",
            87.5: "█",
        },
        divisor: int = types.IECUnit.GiB,
        sleep: int = 3,
        **kwargs,
    ) -> None:
        super().__init__(sleep=sleep, **kwargs)
        self.format = format
        self.colors = colors
        self.icons = icons
        self.divisor = divisor

    def _convert(self, dividend: float) -> float:
        return dividend / self.divisor

    async def run(self) -> None:
        memory = psutil.virtual_memory()

        color = misc.calculate_threshold(self.colors, memory.percent)
        icon = misc.calculate_threshold(self.icons, memory.percent)

        self.update(
            self.ex_format(
                self.format,
                total=self._convert(memory.total),
                available=self._convert(memory.available),
                used=self._convert(memory.used),
                free=self._convert(memory.free),
                percent=memory.percent,
                icon=icon,
            ),
            color=color,
        )
