import time
from collections import namedtuple

import psutil

from i3pyblocks import modules


def test_local_time_module(mocker):
    mocker.patch.object(
        time, "localtime", return_value=time.strptime("Fri Aug 16 21:00:00 2019")
    )

    # Use a non locale dependent format
    instance = modules.LocalTimeModule(format_time="%H:%M:%S", format_date="%y-%m-%d")
    instance.run()

    assert instance.result()["full_text"] == "21:00:00"

    # Simulate click
    instance.click_handler()

    assert instance.result()["full_text"] == "19-08-16"


def test_cpu_percent_module(mocker):
    mocker.patch.object(psutil, "cpu_percent", return_value=75.5)

    instance = modules.psutil.CpuPercentModule(format="{percent}")
    instance.run()

    result = instance.result()

    assert result["full_text"] == "75.5"
    assert result["color"] == modules.Color.WARN


def test_disk_usage_module(mocker):
    sdiskusage = namedtuple("sdiskusage", ["total", "used", "free", "percent"])

    fixture = sdiskusage(
        total=226227036160, used=49354395648, free=165309575168, percent=91.3
    )
    mocker.patch.object(psutil, "disk_usage", return_value=fixture)

    instance = modules.psutil.DiskUsageModule(
        format="{label} {total:.1f} {used:.1f} {free:.1f} {percent}"
    )
    instance.run()

    result = instance.result()

    assert result["full_text"] == "/ 210.7 46.0 154.0 91.3"
    assert result["color"] == modules.Color.URGENT


def test_load_avg_module(mocker):
    mocker.patch.object(psutil, "getloadavg", return_value=(2.5, 5, 15))

    instance = modules.psutil.LoadAvgModule(format="{load1} {load5} {load15}")

    instance.run()

    result = instance.result()

    assert result["full_text"] == "2.5 5 15"
    assert result["color"] == modules.Color.WARN


def test_network_speed_module_down(mocker):
    snicstats = namedtuple("snistats", ["isup", "duplex", "speed", "mtu"])

    fixture_stats = {
        "lo": snicstats(
            isup=True, duplex=psutil.NIC_DUPLEX_UNKNOWN, speed=0, mtu=65536
        ),
        "eno1": snicstats(
            isup=False, duplex=psutil.NIC_DUPLEX_FULL, speed=1000, mtu=1500
        ),
    }
    mocker.patch.object(psutil, "net_if_stats", return_value=fixture_stats)

    instance = modules.psutil.NetworkSpeedModule(
        format_up="{iface} {upload} {download}"
    )

    instance.run()

    result = instance.result()

    assert result["full_text"] == "NO NETWORK"
    assert result["color"] == modules.Color.URGENT


def test_network_speed_module_up(mocker):
    snicstats = namedtuple("snistats", ["isup", "duplex", "speed", "mtu"])

    fixture_stats = {
        "lo": snicstats(
            isup=True, duplex=psutil.NIC_DUPLEX_UNKNOWN, speed=0, mtu=65536
        ),
        "br0": snicstats(
            isup=True, duplex=psutil.NIC_DUPLEX_UNKNOWN, speed=0, mtu=1500
        ),
        "eno1": snicstats(
            isup=True, duplex=psutil.NIC_DUPLEX_FULL, speed=1000, mtu=1500
        ),
    }
    mocker.patch.object(psutil, "net_if_stats", return_value=fixture_stats)

    snetio = namedtuple(
        "snetio", ["bytes_sent", "bytes_recv", "packets_sent", "packets_recv"]
    )

    fixture_previous = {
        "lo": snetio(
            bytes_sent=35052252,
            bytes_recv=35052252,
            packets_sent=72139,
            packets_recv=72139,
        ),
        "virbr0": snetio(bytes_sent=0, bytes_recv=0, packets_sent=0, packets_recv=0),
        "br0": snetio(
            bytes_sent=1058032294,
            bytes_recv=2731067023,
            packets_sent=1939233,
            packets_recv=2579183,
        ),
        "eno1": snetio(
            bytes_sent=1082551675,
            bytes_recv=2778549399,
            packets_sent=2198791,
            packets_recv=2589939,
        ),
    }
    mocker.patch.object(psutil, "net_io_counters", return_value=fixture_previous)

    instance = modules.psutil.NetworkSpeedModule(
        format_up="{iface} {upload} {download}"
    )

    fixture_after = {
        "lo": snetio(
            bytes_sent=35498316,
            bytes_recv=35498316,
            packets_sent=72619,
            packets_recv=72619,
        ),
        "br0": snetio(
            bytes_sent=1068588784,
            bytes_recv=2741492306,
            packets_sent=1944351,
            packets_recv=2581528,
        ),
        "eno1": snetio(
            bytes_sent=1093133039,
            bytes_recv=2789019792,
            packets_sent=2203911,
            packets_recv=2592307,
        ),
    }
    mocker.patch.object(psutil, "net_io_counters", return_value=fixture_after)

    instance.run()

    result = instance.result()

    assert result["full_text"] == "eno1 3.4M 3.3M"
    assert result["color"] == modules.Color.WARN


def test_sensors_battery_module_without_battery(mocker):
    mocker.patch.object(psutil, "sensors_battery", return_value=None)

    instance = modules.psutil.SensorsBatteryModule()

    instance.run()

    result = instance.result()

    assert result["full_text"] == ""


def test_sensors_battery_module_with_battery(mocker):
    sbattery = namedtuple("sbattery", ["percent", "secsleft", "power_plugged"])

    fixture = sbattery(
        percent=93, secsleft=psutil.POWER_TIME_UNLIMITED, power_plugged=True
    )
    mocker.patch.object(psutil, "sensors_battery", return_value=fixture)

    instance = modules.psutil.SensorsBatteryModule()

    instance.run()

    result = instance.result()

    assert result["full_text"] == "B: PLUGGED 93%"

    fixture = sbattery(percent=23, secsleft=16628, power_plugged=False)
    mocker.patch.object(psutil, "sensors_battery", return_value=fixture)

    instance.run()

    result = instance.result()

    assert result["full_text"] == "B: ▂ 23% 4:37:08"
    assert result["color"] == modules.Color.WARN

    fixture = sbattery(
        percent=9, secsleft=psutil.POWER_TIME_UNKNOWN, power_plugged=False
    )
    mocker.patch.object(psutil, "sensors_battery", return_value=fixture)

    instance.run()

    result = instance.result()

    assert result["full_text"] == "B: ▁ 9%"
    assert result["color"] == modules.Color.URGENT


def test_sensors_temperature_module(mocker):
    shwtemp = namedtuple("shwtemp", ["label", "current", "high", "critical"])

    fixture = {
        "coretemp": [
            shwtemp(label="Package id 0", current=78.0, high=82.0, critical=100.0),
            shwtemp(label="Core 0", current=29.0, high=82.0, critical=100.0),
            shwtemp(label="Core 1", current=28.0, high=82.0, critical=100.0),
            shwtemp(label="Core 2", current=28.0, high=82.0, critical=100.0),
            shwtemp(label="Core 3", current=28.0, high=82.0, critical=100.0),
            shwtemp(label="Core 4", current=30.0, high=82.0, critical=100.0),
            shwtemp(label="Core 5", current=28.0, high=82.0, critical=100.0),
        ],
        "acpitz": [
            shwtemp(label="", current=16.8, high=18.8, critical=18.8),
            shwtemp(label="", current=27.8, high=119.0, critical=119.0),
            shwtemp(label="", current=29.8, high=119.0, critical=119.0),
        ],
    }
    mocker.patch.object(psutil, "sensors_temperatures", return_value=fixture)

    instance_default = modules.psutil.SensorsTemperaturesModule(
        format="{label} {current} {high} {critical}"
    )

    instance_default.run()

    result = instance_default.result()

    assert result["full_text"] == "Package id 0 78.0 82.0 100.0"
    assert result["color"] == modules.Color.WARN

    instance_acpitz = modules.psutil.SensorsTemperaturesModule(sensor="acpitz")

    instance_acpitz.run()

    result = instance_acpitz.result()

    assert result["full_text"] == "T: 17°C"


def test_virtual_memory_module(mocker):
    svmem = namedtuple("svmem", ["total", "available", "percent", "used", "free"])

    fixture = svmem(
        total=16758484992,
        available=13300297728,
        percent=95.6,
        used=2631917568,
        free=10560126976,
    )

    mocker.patch.object(psutil, "virtual_memory", return_value=fixture)

    instance = modules.psutil.VirtualMemoryModule(
        format="{total:.1f} {available:.1f} {used:.1f} {free:.1f} {percent}"
    )

    instance.run()

    result = instance.result()

    assert result["full_text"] == "15.6 12.4 2.5 9.8 95.6"
