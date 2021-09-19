import logging
import re

_MAIN_IDENTIFIER = "__main_config__"
MINIMUM_UPDATE_RATE = 0.001

class ConfigParseError(Exception):
    pass

# class ConfigError(Exception):
#     pass

def check_and_convert_type(key, value):
    # float types
    if key in ['update_rate', 'low_value', 'high_value', 'hide_if_over_value', 'hide_if_under_value']:
        try:
            result = float(value)
        except ValueError:
            raise ConfigError("Setting {} should be a number.".format(repr(key)))

    # integer types
    elif key in ['significant_figures', 'zone', 'min_width', 'average_over_samples']:
        try:
            result = int(value)
        except ValueError:
            raise ConfigError("Setting {} should be a non-decimal number.".format(repr(key)))

    # color types
    elif key in ['low_color', 'medium_color', 'high_color']:
        result = value.lower()
        if not re.match(r'#[a-f0-9]{6}|[a-z]+', result):
            fmt_str = "Setting {} formatting not recognized - should be hex (#000000) or text (black)."
            raise ConfigError(fmt_str.format(repr(key)))

    # string types. all are valid, but if config file
    elif key in ['network_down_message']:
        if value is None:
            result = ""
        else:
            result = value

    else:
        result = value

    return result


class ConfigFile():
    def __init__(self, file_handle):
        self.parse_file_handle(file_handle)
        self._check_config()

    def _check_module_config(self, identifier, config_dict):
        if identifier == _MAIN_IDENTIFIER:
            # skip the main config
            return
        if 'low_value' in config_dict or 'high_value' in config_dict:
            if not ('low_color' in config_dict 
                    and 'medium_color' in config_dict 
                    and 'high_color' in config_dict):
                raise ConfigError(
                    ("In {} module {}: When using low_value/high_value, you must "
                    "specify low_color, medium_color, and high_color.").format(
                        config_dict['module'],
                        repr(identifier)))
            if config_dict['high_value'] < config_dict['low_value']:
                raise ConfigError(
                    ("In {} module {}: high_value ({}) must be greater than "
                    "low_value ({})").format(
                        config_dict['module'],
                        repr(identifier),
                        config_dict['high_value'],
                        config_dict['low_value']))
        if 'decimals' in config_dict and 'significant_figures' in config_dict:
            raise ConfigError(
                ("In {} module {}: Only one of 'decimals' and 'significant_figures' "
                "is allowed, not both").format(
                    config_dict['module'],
                    repr(identifier)))
        if (config_dict['update_rate'] != 0 
                and config_dict['update_rate'] < MINIMUM_UPDATE_RATE):
            logging.warning(("In {} module {}: update_rate raised to {}").format(
                config_dict['module'],
                repr(identifier),
                MINIMUM_UPDATE_RATE))
            config_dict['update_rate'] = MINIMUM_UPDATE_RATE

    def _check_config(self):
        for module_identifier in self.config_dictionary:
            self._check_module_config(
                module_identifier,
                self.config_dictionary[module_identifier])

    @property
    def template_replace_character(self):
        try:
            return self.config_dictionary[_MAIN_IDENTIFIER]["template_replace_character"]
        except KeyError:
            return "%"

    @property
    def align_left(self):
        try:
            return self.config_dictionary[_MAIN_IDENTIFIER]["align_left"]
        except KeyError:
            return ""

    @property
    def align_center(self):
        try:
            return self.config_dictionary[_MAIN_IDENTIFIER]["align_center"]
        except KeyError:
            return ""

    @property
    def align_right(self):
        try:
            return self.config_dictionary[_MAIN_IDENTIFIER]["align_right"]
        except KeyError:
            return ""

    @property
    def output_program(self):
        try:
            return self.config_dictionary[_MAIN_IDENTIFIER]["output_program"]
        except KeyError:
            return None
    

    def get_identifiers_from_template_string(self, template_string):
        return template_string.split(self.template_replace_character)[1::2]

    def get_constant_text_from_template_string(self, template_string):
        return template_string.split(self.template_replace_character)[::2]

    def get_config_dict_by_identifier(self, identifier):
        if identifier.lower() == 'stdinreader':
            return {}
        else:
            try:
                return self.config_dictionary[identifier]
            except KeyError:
                fmt_str = (
                    "Invalid identifier {} found in format string, but was not "
                    "defined in config.")
                raise ConfigParseError(fmt_str.format(repr(identifier)))

    def get_module_type_by_identifier(self, identifier):
        if identifier.lower() == 'stdinreader':
            return 'stdinreader'
        else:
            return self.get_config_dict_by_identifier(identifier)['module']

    def print_all_values(self):
        import pprint
        pprint.pprint(self.config_dictionary)

    def parse_file_handle(self, file_handle):
        current_module = "main"
        identifier = _MAIN_IDENTIFIER
        config_dictionary = {}
        config_dictionary[identifier] = {}

        for idx, line in enumerate(file_handle):
            line_number = idx + 1
            line = line.strip()
            if line == "" or line.startswith("#"):
                continue

            match = re.match(r'Module ([a-zA-Z]+) as ([a-zA-Z_]+):', line)
            if match:
                current_module = match.group(1).lower()
                identifier = match.group(2)

                if identifier in config_dictionary:
                    raise ConfigParseError(
                        "Line {}: Found duplicate definition for identifier '{}'.".format(line_number, identifier))

                config_dictionary[identifier] = {}
                config_dictionary[identifier]['module'] = current_module
                continue

            match = re.match(r'^([a-zA-Z_]+): ?(.*)', line)
            #print('line', line_number, '{}'.format(repr(line)), 'match' if match else 'no match')
            if match:
                key = match.group(1).lower()
                value = match.group(2)
                try:
                    value = check_and_convert_type(key, value)
                except ConfigParseError as e:
                    raise ConfigParseError("Line {}: {}".format(line_number, e))
                config_dictionary[identifier][key] = value
                continue

            raise ConfigParseError("Line {}: Error parsing line.".format(line_number))

        self.config_dictionary = config_dictionary


                





