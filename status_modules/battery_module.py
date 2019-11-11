import time
import subprocess
import re

from .prototype_module import PrototypeModule



# threshold under which battery is considered "charged" in milliamps
_CHARGE_MODE_THRESHOLD_MA = 5


def run_command(cmd):
    """Run a command and return its stdout as a string. Command must be passed
    as a list of parameters ie ['ls', '-la']"""
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.decode('utf-8')


def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()


class Battery():
    """Wrapper around battery stats.

    TODO: remove leftipat and (maybe) main template, since only acstatus is used.
    """
    def __init__(self, identifier="BAT0"):
        self._prefix = "/sys/class/power_supply/" + identifier + "/"
        self.identifier = identifier

    @property
    def manufacturer(self):
        return read_file(self._prefix + "manufacturer").strip()

    @property
    def model(self):
        return read_file(self._prefix + "model_name").strip()

    @property
    def voltage(self):
        val_ua = int(read_file(self._prefix + "voltage_now"))
        return val_ua / 1000000.0

    @property
    def current_draw_amps(self):
        try:
            val_ua = int(read_file(self._prefix + "current_now"))
        except OSError:
            # this file may not exist for a few seconds after AC is plugged in.
            # return 0 in this case (not ideal; it indicates idle) until I can think
            # of something better
            return 0
        else:
            return val_ua / 1000000.0
    
    @property
    def watts(self):
        return self.voltage * self.current_draw_amps

    @property
    def capacity_now_amphours(self):
        val_uah = int(read_file(self._prefix +"charge_now"))
        return val_uah / 1000000.0

    @property
    def capacity_full_amphours(self):
        val_uah = int(read_file(self._prefix +"charge_full"))
        return val_uah / 1000000.0

    @property
    def capacity_full_design_amphours(self):
        val_uah = int(read_file(self._prefix +"charge_full_design"))
        return val_uah / 1000000.0

    @property
    def charge_percent(self):
        val = 100.0 * self.capacity_now_amphours / self.capacity_full_amphours
        if val > 100:
            val = 100
        elif val < 0:
            val = 0

        return val 

    @property
    def health_percent(self):
        val = 100.0 * self.capacity_full_amphours / self.capacity_full_design_amphours
        if val > 100:
            val = 100
        elif val < 0:
            val = 0

        return val

    @property
    def health_percent_readable(self):
        return "{:.0f}".format(self.health_percent)

    @property
    def status(self):
        """Determine the _real_ state of the battery using the current draw, output
        of tlp-stat, and /sys status.
        
        Returns one of "Charging", "Discharging", or "AC Idle"
        """
        sys_class_status = read_file(self._prefix + "status").strip()

        # tlp_output = run_command('tlp-stat -s')
        # tlp_status = None
        # for line in tlp_output:
        #     re.match("^Mode\W+=\W+(?P<mode>.+)$", line)
        #     if match:
        #         tlp_status = match.group(1)
        # if tlp_status is None:
        #     raise RuntimeError("Failed to parse 'tlp-stat -s' output")

        if (self.current_draw_amps * 1000.0) > _CHARGE_MODE_THRESHOLD_MA:
            # if current is flowing battery is either charging or discharging
            if sys_class_status == "Charging":
                return "Charging"
            if sys_class_status == "Unknown":
                return "Discharging"
            if sys_class_status == "Discharging":
                return "Discharging"
        else:
            # no current through battery so must be idling on AC
            return "AC Idle"

    @property
    def time_left_readable(self):
        val = self.time_left_readable_include_seconds
        if val is "":
            return ""
        else:
            return val[:-3]

    @property
    def time_left_readable_include_seconds(self):
        if self.identifier.startswith('BAT'):
            # pull number off the end of identifier and use when search acpi output
            desired_battery_id = self.identifier[3:]

        acpi_battery_info = run_command(['acpi', '-b'])

        # regex matches both these strings, named group 'time_left' is optional:
        #     Battery 0: Discharging, 96%, 05:25:42 remaining
        #     Battery 0: Full, 100%
        # also noticed these (for a few seconds after AC is plugged in), these are
        # caught before running the regex
        #     Battery 0: Charging, 98%, rate information unavailable
        #     Battery 0: Unknown, 95%, rate information unavailable
        #     Battery 0: Unknown, 95%
        #     Battery 0: Full, 100%,  until charged
        regex_str = "^Battery (?P<id>\d+): (?P<status>\w+), (?P<charge_percent>\d+)%(?:, (?P<time_left>[\d:]+) (remaining|until charged))*$"
        for line in acpi_battery_info.split('\n'):
            # for lines which basically say "I don't know", fallback on 00:00:00
            if line.startswith("Battery {}".format(desired_battery_id)):
                if ("Unknown" in line 
                        or "rate information unavailable" in line
                        or "100%,  until charged" in line):
                    return "00:00:00"
            match = re.match(regex_str, line)
            if match:
                battery_id, status, charge_percent, time_left, suffix = match.groups()
                time_left = "" if time_left is None else time_left
                if battery_id == desired_battery_id:
                    # trim off seconds if show_seconds is false
                    return time_left
        raise RuntimeError("Failed to find battery info in 'acpi -b' output")

    @property
    def time_left_seconds(self):
        val = self.time_left_readable_include_seconds
        if val is "":
            return ""
        else:
            hours, minutes, seconds = [int(n) for n in val.split(":")]
            return (hours * 3600) + (minutes * 60) + seconds

    def format_status(
            self,
            template,
            low_threshold=None,
            high_threshold=None,
            low_color=None,
            normal_color=None,
            high_color=None,
            on_ac_status=None,
            off_ac_status=None,
            idle_ac_status=None,
            on_icon_pattern=None,
            off_icon_pattern=None,
            idle_icon_pattern=None,
            bar_width=None):
        """Format a string with the current battery state."""

        if bar_width is None:
            bar_width = 10

        if low_threshold is None:
            low_threshold = 33

        if high_threshold is None:
            high_threshold = 66

        if on_icon_pattern is None:
            on_icon_pattern = ""

        if off_icon_pattern is None:
            off_icon_pattern = ""

        if idle_icon_pattern is None:
            idle_icon_pattern = ""

        if on_ac_status is None:
            on_ac_status = "Charging"

        if off_ac_status is None:
            off_ac_status = "Discharging"

        if idle_ac_status is None:
            idle_ac_status = "Charged"

        try:
            charge = self.charge_percent
        except Exception as e:
            logging.error("No battery")
            return "No Battery"

        scale_val = 100 / bar_width
        leftbar = "#" * round(charge / scale_val) + ":" * round(
            (100 - charge) / scale_val
        )

        status = self.status
        if status == "Charging":
            ac_status = on_ac_status
            leftipat = on_icon_pattern
        elif status == "Discharging":
            ac_status = off_ac_status
            leftipat = off_icon_pattern
        elif status == "AC Idle":
            ac_status = idle_ac_status
            leftipat = idle_icon_pattern

        # # scale 0-100 (101 values) to 0-8 (9 values)
        # leftipat = leftipat.replace("%%", "{:02d}".format(int(9*charge/101.0)))
        # # scale 0-100 (101 values) to 0-15 (16 values)
        # leftipat = leftipat.replace("$$", "{:02d}".format(int(16*charge/101.0)))
        # # scale 0-100 (101 values) to 0-99 (100 values)
        # leftipat = leftipat.replace("@@", "{:02d}".format(int(100*charge/101.0)))

        # scale 0-100 (101 values) to 0-8 (9 values)
        ac_status = ac_status.replace("%%", "{:02d}".format(int(9*charge/101.0)))
        # scale 0-100 (101 values) to 0-15 (16 values)
        ac_status = ac_status.replace("$$", "{:02d}".format(int(16*charge/101.0)))
        # scale 0-100 (101 values) to 0-99 (100 values)
        ac_status = ac_status.replace("@@", "{:02d}".format(int(100*charge/101.0)))

        charge_str = "{:.0f}".format(charge)
        if charge < float(low_threshold) and low_color is not None:
            color = low_color
            charge_str = "<fc={}>{}</fc>".format(color, charge_str)
        elif charge < float(high_threshold) and normal_color is not None:
            color = normal_color
            charge_str = "<fc={}>{}</fc>".format(color, charge_str)
        elif high_color is not None:
            color = high_color
            charge_str = "<fc={}>{}</fc>".format(color, charge_str)

        # replace acstatus/leftipat first - if they contain <variables> they will be replaced
        template = template.replace("<acstatus>", ac_status)
        template = template.replace("<leftipat>", leftipat)
        template = template.replace("<watts>", "{:.1f}".format(self.watts))
        template = template.replace("<left>", charge_str)
        template = template.replace("<leftbar>", leftbar)
        template = template.replace("<timeleft>", self.time_left_readable)
        template = template.replace("<health>", self.health_percent_readable)
        return template

class BatteryModule(PrototypeModule):

    _required_keys = ['charging_template', 'discharging_template', 'idle_template']
    _default_config_dict = {}

    def __init__(self):
        self._battery = Battery(identifier="BAT0")
        super().__init__()

    def _run(self):

        return self._battery.format_status(
            '<acstatus>',
            low_threshold=None if 'low_value' not in self.config_dict else self.config_dict['low_value'],
            high_threshold=None if 'high_value' not in self.config_dict else self.config_dict['high_value'],
            low_color=None if 'low_color' not in self.config_dict else self.config_dict['low_color'],
            normal_color=None if 'medium_color' not in self.config_dict else self.config_dict['medium_color'],
            high_color=None if 'high_color' not in self.config_dict else self.config_dict['high_color'],
            on_ac_status=None if 'charging_template' not in self.config_dict else self.config_dict['charging_template'],
            off_ac_status=None if 'discharging_template' not in self.config_dict else self.config_dict['discharging_template'],
            idle_ac_status=None if 'idle_template' not in self.config_dict else self.config_dict['idle_template'],
            bar_width=None if 'bar_width' not in self.config_dict else self.config_dict['bar_width'])
