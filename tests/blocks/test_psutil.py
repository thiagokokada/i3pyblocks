from pathlib import Path
from unittest.mock import Mock

import psutil
import pytest
from helpers import misc

from i3pyblocks import types
from i3pyblocks.blocks import psutil as m_psutil


@pytest.mark.asyncio
async def test_cpu_percent_block():
    mock_psutil = Mock(psutil)
    mock_psutil.cpu_percent.return_value = 75.5

    instance = m_psutil.CpuPercentBlock(format="{percent}", _psutil=mock_psutil)
    await instance.run()

    result = instance.result()

    assert result["full_text"] == "75.5"
    assert result["color"] == types.Color.WARN


@pytest.mark.asyncio
async def test_disk_usage_block():
    mock_psutil = Mock(psutil)
    mock_psutil.disk_usage.return_value = misc.AttributeDict(
        total=226227036160, used=49354395648, free=165309575168, percent=91.3
    )

    instance = m_psutil.DiskUsageBlock(
        format="{icon} {label} {total:.1f} {used:.1f} {free:.1f} {percent}",
        _psutil=mock_psutil,
    )
    await instance.run()

    result = instance.result()

    assert result["full_text"] == "█ / 210.7 46.0 154.0 91.3"
    assert result["color"] == types.Color.URGENT


@pytest.mark.asyncio
async def test_disk_usage_block_with_short_label():
    mock_psutil = Mock(psutil)
    mock_psutil.disk_usage.return_value = misc.AttributeDict(
        total=226227036160, used=49354395648, free=165309575168, percent=91.3
    )
    path_str = "/media/backup/Downloads"

    instance = m_psutil.DiskUsageBlock(
        path=Path(path_str),
        format="{label}",
        short_label=True,
        _psutil=mock_psutil,
    )
    await instance.run()

    # Making sure that we call psutil.disk_usage with str instead of Path
    mock_psutil.disk_usage.assert_called_once_with(path_str)

    result = instance.result()

    assert result["full_text"] == "/m/b/D"


@pytest.mark.asyncio
async def test_load_avg_block():
    mock_psutil = Mock(psutil)
    mock_psutil.getloadavg.return_value = (2.5, 5, 15)

    instance = m_psutil.LoadAvgBlock(
        format="{load1} {load5} {load15}",
        colors=(
            (0, types.Color.NEUTRAL),
            (2, types.Color.WARN),
            (4, types.Color.URGENT),
        ),
        _psutil=mock_psutil,
    )

    await instance.run()

    result = instance.result()

    assert result["full_text"] == "2.5 5 15"
    assert result["color"] == types.Color.WARN


@pytest.mark.asyncio
async def test_network_speed_block_down():
    mock_psutil = Mock(psutil)
    mock_psutil.net_if_stats.return_value = {
        "lo": misc.AttributeDict(
            isup=True, duplex=psutil.NIC_DUPLEX_UNKNOWN, speed=0, mtu=65536
        ),
        "eno1": misc.AttributeDict(
            isup=False, duplex=psutil.NIC_DUPLEX_FULL, speed=1000, mtu=1500
        ),
    }

    instance = m_psutil.NetworkSpeedBlock(
        format_up="{interface} {upload} {download}", _psutil=mock_psutil
    )

    await instance.run()

    result = instance.result()

    assert result["full_text"] == "NO NETWORK"
    assert result["color"] == types.Color.URGENT


@pytest.mark.asyncio
async def test_network_speed_block_up():
    mock_psutil = Mock(psutil)
    mock_psutil.net_if_stats.return_value = {
        "lo": misc.AttributeDict(
            isup=True, duplex=psutil.NIC_DUPLEX_UNKNOWN, speed=0, mtu=65536
        ),
        "eno1": misc.AttributeDict(
            isup=True, duplex=psutil.NIC_DUPLEX_FULL, speed=1000, mtu=1500
        ),
    }

    mock_psutil.net_io_counters.side_effect = [
        {
            "lo": misc.AttributeDict(
                bytes_sent=35052252,
                bytes_recv=35052252,
                packets_sent=72139,
                packets_recv=72139,
            ),
            "eno1": misc.AttributeDict(
                bytes_sent=1082551675,
                bytes_recv=2778549399,
                packets_sent=2198791,
                packets_recv=2589939,
            ),
        },
        {
            "lo": misc.AttributeDict(
                bytes_sent=35498316,
                bytes_recv=35498316,
                packets_sent=72619,
                packets_recv=72619,
            ),
            "eno1": misc.AttributeDict(
                bytes_sent=1093133039,
                bytes_recv=2789019792,
                packets_sent=2203911,
                packets_recv=2592307,
            ),
        },
    ]

    instance = m_psutil.NetworkSpeedBlock(
        format_up="{interface} {upload} {download}", _psutil=mock_psutil
    )

    await instance.run()

    result = instance.result()

    assert result["full_text"] == "eno1 3.4M 3.3M"
    assert result["color"] == types.Color.WARN


@pytest.mark.asyncio
async def test_sensors_battery_block_without_battery():
    mock_psutil = Mock(psutil)
    mock_psutil.sensors_battery.return_value = None

    instance = m_psutil.SensorsBatteryBlock(_psutil=mock_psutil)

    await instance.run()

    result = instance.result()

    assert result["full_text"] == ""


@pytest.mark.asyncio
async def test_sensors_battery_block_with_battery():
    mock_psutil = Mock(psutil)
    mock_psutil.sensors_battery.side_effect = [
        misc.AttributeDict(
            percent=93, secsleft=psutil.POWER_TIME_UNLIMITED, power_plugged=True
        ),
        misc.AttributeDict(percent=23, secsleft=16628, power_plugged=False),
        misc.AttributeDict(
            percent=9, secsleft=psutil.POWER_TIME_UNKNOWN, power_plugged=False
        ),
    ]

    instance = m_psutil.SensorsBatteryBlock(_psutil=mock_psutil)

    await instance.run()

    result = instance.result()

    assert result["full_text"] == "B: PLUGGED 93%"

    await instance.run()

    result = instance.result()

    assert result["full_text"] == "B: ▂ 23% 4:37:08"
    assert result["color"] == types.Color.WARN

    await instance.run()

    result = instance.result()

    assert result["full_text"] == "B: ▁ 9%"
    assert result["color"] == types.Color.URGENT


@pytest.mark.asyncio
async def test_sensors_temperature_block():
    mock_psutil = Mock(psutil)
    mock_psutil.sensors_temperatures.return_value = {
        "coretemp": [
            misc.AttributeDict(
                label="Package id 0", current=78.0, high=82.0, critical=100.0
            ),
            misc.AttributeDict(label="Core 0", current=29.0, high=82.0, critical=100.0),
            misc.AttributeDict(label="Core 1", current=28.0, high=82.0, critical=100.0),
            misc.AttributeDict(label="Core 2", current=28.0, high=82.0, critical=100.0),
            misc.AttributeDict(label="Core 3", current=28.0, high=82.0, critical=100.0),
            misc.AttributeDict(label="Core 4", current=30.0, high=82.0, critical=100.0),
            misc.AttributeDict(label="Core 5", current=28.0, high=82.0, critical=100.0),
        ],
        "acpitz": [
            misc.AttributeDict(label="", current=16.8, high=18.8, critical=18.8),
            misc.AttributeDict(label="", current=27.8, high=119.0, critical=119.0),
            misc.AttributeDict(label="", current=29.8, high=119.0, critical=119.0),
        ],
    }

    instance_default = m_psutil.SensorsTemperaturesBlock(
        format="{icon} {label} {current} {high} {critical}", _psutil=mock_psutil
    )

    await instance_default.run()

    result = instance_default.result()

    assert result["full_text"] == "▇ Package id 0 78.0 82.0 100.0"
    assert result["color"] == types.Color.WARN

    instance_acpitz = m_psutil.SensorsTemperaturesBlock(
        sensor="acpitz", _psutil=mock_psutil
    )

    await instance_acpitz.run()

    result = instance_acpitz.result()

    assert result["full_text"] == "T: 17°C"


@pytest.mark.asyncio
async def test_virtual_memory_block():
    mock_psutil = Mock(psutil)
    mock_psutil.virtual_memory.return_value = misc.AttributeDict(
        total=16758484992,
        available=13300297728,
        percent=95.6,
        used=2631917568,
        free=10560126976,
    )

    instance = m_psutil.VirtualMemoryBlock(
        format="{icon} {total:.1f} {available:.1f} {used:.1f} {free:.1f} {percent}",
        _psutil=mock_psutil,
    )

    await instance.run()

    result = instance.result()

    assert result["full_text"] == "█ 15.6 12.4 2.5 9.8 95.6"
