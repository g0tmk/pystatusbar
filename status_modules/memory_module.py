import subprocess
import shlex
import logging

from .prototype_module import PrototypeModule


def _get_memory_used_percentage():

    meminfo_stats = {}
    for idx, line in enumerate(open("/proc/meminfo", "r")):
        try:
            split_values = line.split()
            label = split_values[0]
            value = int(split_values[1])
            meminfo_stats[label] = value
        except (ValueError, IndexError):
            logging.exception("Bad response from '/proc/meminfo': {}".format(repr(line)))
            return 0

        # only need to read the first 5 lines
        if idx == 4:
            break

    # MemTotal:       16294428 kB
    # MemFree:        11929748 kB
    # MemAvailable:   13025336 kB
    # Buffers:          388424 kB
    # Cached:          1146084 kB
    total = meminfo_stats['MemTotal:']
    #free = meminfo_stats['MemFree:']
    free = meminfo_stats['MemAvailable:']

    return 100 * (total - free) / total

class MemoryModule(PrototypeModule):

    _required_keys = []
    _default_config_dict = {
        "template": "<usedratio>%",
        "decimals": "0",
    }

    def _run(self):
        template = self.config_dict['template'][:]

        used_ratio = _get_memory_used_percentage()
        used_ratio = self._format_value(used_ratio, self.config_dict)

        template = template.replace('<usedratio>', used_ratio)
        return template

