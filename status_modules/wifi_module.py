import subprocess
import re
import sys

from .prototype_module import PrototypeModule

# constant for now - it seems to always be in the same location
_IWCONFIG_BINARY = "/sbin/iwconfig"


def run_command(cmd):
    """Run a command and return its stdout as a string. Command must be passed
    as a list of parameters ie ['ls', '-la']"""
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.decode('utf-8')


def get_wireless_info():
    """Returns wireless AP and quality (in percent) as a tuple."""
    iwconfig_output = run_command(_IWCONFIG_BINARY)
    for line in iwconfig_output.split("\n"):
        # look for line containing essid, save if its a match
        match = re.match('^[a-zA-Z0-9]+.+ESSID:"(.+)"', line)
        if match:
            essid = match.group(1)
        # if we find the quality line, return
        match = re.match('^\s+Link Quality=(\d+)/(\d+)', line)
        if match:
            quality = 100 * float(match.group(1)) / float(match.group(2))
            return essid, quality
        
    return None, None

def get_formatted_wireless_info(
        template,
        low_threshold=None,
        high_threshold=None,
        low_color=None,
        medium_color=None,
        high_color=None,
        suffix=None,
        bar_width=None):
    essid, quality = get_wireless_info()
    if essid is None:
        return "Wifi not connected"
        sys.exit(0)

    if low_threshold is None:
        low_threshold = 33

    if high_threshold is None:
        high_threshold = 66

    if suffix is None:
        suffix = False

    if bar_width is None:
        bar_width = 10

    # make 'short' name by trimming words to 3 chars
    essid_short = ' '.join([word[:3] for word in essid.split()])

    if quality < float(low_threshold):
        color = low_color
    elif quality < float(high_threshold):
        color = medium_color
    else:
        color = high_color

    if quality > 100:
        quality = 100
    if quality < 0:
        quality = 0

    scale_val = 100 / bar_width
    qualitybar = "#" * round(quality / scale_val) + ":" * round(
        (100 - quality) / scale_val
    )

    # scale 0-100 (101 values) to 0-8 (9 values)
    template = template.replace("%%", "{:02d}".format(int(9*quality/101.0)))

    quality = "{:.0f}".format(quality)
    if color is not None:
        quality = "<fc={}>{}</fc>".format(color, quality)
    if suffix:
        quality += "%"

    template = template.replace("<essid>", essid)
    template = template.replace("<essid_short>", essid_short)
    template = template.replace("<quality>", quality)
    template = template.replace("<qualitybar>", qualitybar)
    return template







class WifiModule(PrototypeModule):

    _required_keys = []
    _default_config_dict = {
        'template': '<essid>:<quality>'
    }

    def _run(self):

        return get_formatted_wireless_info(
            self.config_dict['template'],
            low_threshold=None if 'low_value' not in self.config_dict else self.config_dict['low_value'],
            high_threshold=None if 'high_value' not in self.config_dict else self.config_dict['high_value'],
            low_color=None if 'low_color' not in self.config_dict else self.config_dict['low_color'],
            medium_color=None if 'medium_color' not in self.config_dict else self.config_dict['medium_color'],
            high_color=None if 'high_color' not in self.config_dict else self.config_dict['high_color'],
            suffix=None if 'suffix' not in self.config_dict else self.config_dict['suffix'],
            bar_width=None if 'bar_width' not in self.config_dict else self.config_dict['bar_width'])
