
from ..configfile import ConfigParseError

from .date_module import DateModule
from .command_module import CommandModule
from .cpu_module import CPUModule
from .temperature_module import TemperatureModule
from .memory_module import MemoryModule
from .network_module import NetworkModule
from .battery_module import BatteryModule
from .wifi_module import WifiModule


def lookup_module(module_name):
    lookup_table = {
        'date': date_module.DateModule,
        'command': command_module.CommandModule,
        'cpu': cpu_module.CPUModule,
        'temperature': temperature_module.TemperatureModule,
        'memory': memory_module.MemoryModule,
        'network': network_module.NetworkModule,
        'battery': battery_module.BatteryModule,
        'wifi': wifi_module.WifiModule,
    }
    try:
        return lookup_table[module_name.lower()]
    except KeyError:
        raise ConfigParseError("Unknown module '{}'".format(module_name))


