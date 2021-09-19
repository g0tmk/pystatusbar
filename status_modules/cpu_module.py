import subprocess
import shlex

from .prototype_module import PrototypeModule

class CPUModule(PrototypeModule):

    _required_keys = []
    _default_config_dict = {
        "template": "<total>%",
        "decimals": 0,
    }
    _sample_record = []

    def _get_cpu_percentage(self):
        # user    nice   system  idle      iowait irq   softirq  steal  guest  guest_nice
        # cpu  74608   2520   24433   1117073   6176   4054  0        0      0      0

        # PrevIdle = previdle + previowait
        # Idle = idle + iowait

        # PrevNonIdle = prevuser + prevnice + prevsystem + previrq + prevsoftirq + prevsteal
        # NonIdle = user + nice + system + irq + softirq + steal

        # PrevTotal = PrevIdle + PrevNonIdle
        # Total = Idle + NonIdle

        # # differentiate: actual value minus the previous one
        # totald = Total - PrevTotal
        # idled = Idle - PrevIdle

        # CPU_Percentage = (totald - idled)/totald

        for line in open("/proc/stat", "r"):
            _, user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice = line.split()
            break

        idle_total = int(idle) + int(iowait)
        non_idle_total = int(user) + int(nice) + int(system) + int(irq) + int(softirq) + int(steal)
        total = int(idle_total) + int(non_idle_total)

        try:
            self._prev_total
        except AttributeError:
            output = 0
        else:
            total_diff = total - self._prev_total
            idle_diff = idle_total - self._prev_idle_total

            cpu_percentage = (total_diff - idle_diff) / total_diff
            output = cpu_percentage

        self._prev_idle_total = idle_total
        self._prev_total = total

        return output

    def _run(self):
        template = self.config_dict['template'][:]

        if 'hide_if_under_value' in self.config_dict:
            hide_if_under_value = self.config_dict['hide_if_under_value']
        else:
            hide_if_under_value = 0

        if 'hide_if_over_value' in self.config_dict:
            hide_if_over_value = self.config_dict['hide_if_over_value']
        else:
            hide_if_over_value = 100

        if 'average_over_samples' in self.config_dict:
            average_over_samples = self.config_dict['average_over_samples']
        else:
            average_over_samples = 1

        cpu_percentage = self._get_cpu_percentage() * 100

        # TODO: move the average_over_samples functionality to a PrototypeModule method
        # average the samples
        if average_over_samples > 1:
            self._sample_record.append(cpu_percentage)
            # trim the list to the desired number of samples
            self._sample_record = self._sample_record[-average_over_samples:]
            # calc average
            cpu_percentage = sum(self._sample_record) / len(self._sample_record)

        # hide the whole template if configured to hide it
        if cpu_percentage < hide_if_under_value or cpu_percentage > hide_if_over_value:
            return ''

        cpu_percentage = self._format_value(cpu_percentage, self.config_dict)

        template = template.replace('<total>', cpu_percentage)
        return template

