import time
from ..configfile import ConfigParseError

def format_number_basic(number, decimal_places=None, min_width=None):
    if decimal_places is None:
        decimal_places = 0

    fmt_str = "{:." + decimal_places + "f}"
    output = fmt_str.format(number)

    if min_width is not None:
        # is min width is set, expand output with spaces and align values to the right
        fmt_str = "{:>" + str(min_width) + "}"
        output = fmt_str.format(output)

    return output

def format_number_thousands(number, suffix_list, smallest_suffix=None, decimal_places=None, min_width=None):
    if smallest_suffix is None:
        smallest_suffix = suffix_list[0]
    if decimal_places is None:
        decimal_places = 0

    current_suffix_idx = 0

    try:
        while smallest_suffix not in suffix_list[current_suffix_idx]:
            current_suffix_idx += 1
            number /= 1000.0
    except IndexError:
        raise ConfigParseError("Could not find unit {}".format(repr(smallest_suffix)))

    while number >= 1000:
        current_suffix_idx += 1
        number /= 1000.0
        # stop searching if we reach the last suffix
        if current_suffix_idx == len(suffix_list) - 1:
            break

    fmt_str = "{:." + decimal_places + "f}{}"
    output = fmt_str.format(number, suffix_list[current_suffix_idx])

    if min_width is not None:
        # is min width is set, expand output with spaces and align values to the right
        fmt_str = "{:>" + str(min_width) + "}"
        output = fmt_str.format(output)

    return output


class PrototypeModule():
    def __init__(self):
        self._update_rate = None
        self._last_run_time = None
        self._cached_output = None

    def _format_value(self, value, config_dict, unit_type=None):
        color = None
        if 'low_value' in config_dict and value < config_dict['low_value']:
            color = config_dict['low_color']
        elif 'high_value' in config_dict and value < config_dict['high_value']:
            color = config_dict['medium_color']
        elif 'high_value' in config_dict and value >= config_dict['high_value']:
            color = config_dict['high_color']

        if 'smallest_unit' in config_dict:
            smallest_unit = config_dict['smallest_unit']
        else:
            smallest_unit = None

        if 'min_width' in config_dict:
            min_width = config_dict['min_width']
        else:
            min_width = None

        decimal_places = config_dict['decimals']

        if unit_type == 'bytes':
            units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
            formatted_number = format_number_thousands(value, units, smallest_unit, decimal_places, min_width)
        elif unit_type == 'bytes/s':
            units = ['B/s', 'KB/s', 'MB/s', 'GB/s', 'TB/s', 'PB/s', 'EB/s', 'ZB/s', 'YB/s']
            formatted_number = format_number_thousands(value, units, smallest_unit, decimal_places, min_width)
        else:
            formatted_number = format_number_basic(value, decimal_places, min_width)

        if color is None:
            return formatted_number
        else:
            return "<fc={}>{}</fc>".format(color, formatted_number)

    def run_cached(self, update_rate=None):
        if update_rate == None:
            update_rate = self._update_rate
        
        now = time.time()
        # if never run before, run it
        if self._last_run_time is None:
            need_to_run = True
        # if update rate is not 0 (periodic updates), and time is up, run it
        elif update_rate != 0 and now > self._last_run_time + update_rate:
            need_to_run = True
        else:
            need_to_run = False

        if need_to_run:
            self._cached_output = self._run()
            self._last_run_time = now

        return self._cached_output

    @classmethod
    def from_config_dict(cls, config_dict):
        instance = cls()
        instance.config_dict = instance._default_config_dict.copy()

        try:
            instance._update_rate = float(config_dict["update_rate"])
        except KeyError:
            raise ConfigParseError("Could not find required option 'update_rate' for module {}.".format(
                config_dict["module"]))
        except TypeError:
            raise ConfigParseError("Option 'update_rate' for module {} should be a number.".format(
                config_dict["module"]))

        for key in instance._required_keys:
            if key not in config_dict:
                raise ConfigParseError("Could not find required option '{}' for module {}.".format(
                    key,
                    config_dict["module"]))

        for key in config_dict:
            if key in ["update_rate", "module"]:
                pass
            else:
                instance.config_dict[key] = config_dict[key]

        return instance