import subprocess
import shlex
import logging

from .prototype_module import PrototypeModule
from ..configfile import ConfigError


def _get_temp_degrees_c_thermalzone(zone):
    path = "/sys/class/thermal/thermal_zone{}/temp".format(zone)
    try:
        with open(path, "r") as handle:
            response = handle.readline().strip()
    except OSError:
        raise ConfigError("Failed to read from '{}'".format(path))

    try:
        temp_degrees_c = float(response) / 1000.0
    except TypeError as e:
        logging.exception("Got unexpected data ({}) from path {}.".format(response, path))
        return 0
    else:
        return temp_degrees_c

class TemperatureModule(PrototypeModule):
    _required_keys = ["type"]
    _default_config_dict = {
        "template": "<temp>C",
        "decimals": "0",
    }

    def _run(self):
        if self.config_dict['type'] in ["thermalzone", "thermal_zone"]:
            try:
                self.config_dict['zone']
            except KeyError:
                raise ConfigError("Could not find 'zone' defined for Temperature module.")
            else:
                temp_degrees_c = _get_temp_degrees_c_thermalzone(self.config_dict['zone'])
        else:
            raise ConfigError("Unsupported Temperature module type {}".format(repr(self.config_dict['type'])))

        temp_degrees_c = self._format_value(temp_degrees_c, self.config_dict)

        template = self.config_dict['template'][:]
        template = template.replace('<temp>', temp_degrees_c)

        return template







