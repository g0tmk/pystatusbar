import subprocess
import shlex
import logging
import time

from .prototype_module import PrototypeModule


def _get_default_network_adapter():
    # default via 10.0.0.1 dev wlp2s0 
    # 10.0.0.0/24 dev wlp2s0 proto kernel scope link src 10.0.0.233 
    # 192.168.122.0/24 dev virbr0 proto kernel scope link src 192.168.122.1 linkdown 

    completed_process = subprocess.run(['ip', 'route', 'list'], stdout=subprocess.PIPE)
    first_output_line = completed_process.stdout.decode("utf-8").split('\n')[0]
    try:
        split_line_values = first_output_line.split()
        ip = split_line_values[2]
        dev = split_line_values[4]

        link_is_down = False
        try:
            if split_line_values[5] == "linkdown":
                link_is_down = True
        except IndexError:
            pass

    except ValueError:
        raise RuntimeError("Unexpected response from 'ip route': {}".format(repr(first_output_line)))
    else:
        return dev

class NetworkModule(PrototypeModule):

    _required_keys = []
    _default_config_dict = {
        "template": "<usedratio>%",
        "decimals": "0",
    }

    def _calculate_transfer_speed(self, current_receive_bytes, current_transmit_bytes):
        time_now = time.time()

        try:
            self._prev_time
        except AttributeError:
            output = 0, 0
        else:
            receive_byte_diff = current_receive_bytes - self._prev_receive_bytes
            transmit_byte_diff = current_transmit_bytes - self._prev_transmit_bytes
            time_diff = time_now - self._prev_time
            output = receive_byte_diff / time_diff, transmit_byte_diff / time_diff

        self._prev_receive_bytes = current_receive_bytes
        self._prev_transmit_bytes = current_transmit_bytes
        self._prev_time = time_now

        return output

    def _get_network_transfer_speeds(self, interface=None):
        # Inter-|   Receive                                                |  Transmit
        #  face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
        # wlp2s0: 2138254605 1554703    0    0    0     0          0         0 35875368  286177    0    0    0     0       0          0
        #     lo:    6464      84    0    0    0     0          0         0     6464      84    0    0    0     0       0          0
        # virbr0:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
        # virbr0-nic:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0

        if interface is None:
            interface = _get_default_network_adapter()

        for line in open("/proc/net/dev", "r"):
            line = line.strip()
            if line.startswith(interface):
                values = line.split()
                try:
                    receive_bytes = int(values[1])
                    transmit_bytes = int(values[9])
                except (ValueError, IndexError):
                    logging.exception("Bad response from '/proc/net/dev': {}".format(repr(line)))
                    return interface, 0, 0
                receive_speed, transmit_speed = self._calculate_transfer_speed(receive_bytes, transmit_bytes)
                return interface, receive_speed, transmit_speed
            else:
                continue

        raise RuntimeError("Could not find device '{}' in output of /proc/net/dev".format(interface))

    def _run(self):
        template = self.config_dict['template'][:]

        interface, receive_speed, transmit_speed = self._get_network_transfer_speeds()
        receive_speed = self._format_value(
            receive_speed,
            self.config_dict,
            unit_type='bytes/s')
        transmit_speed = self._format_value(
            transmit_speed,
            self.config_dict,
            unit_type='bytes/s')

        template = template.replace('<rx>', receive_speed)
        template = template.replace('<tx>', transmit_speed)
        template = template.replace('<dev>', interface)
        return template

