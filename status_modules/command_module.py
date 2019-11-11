import subprocess
import shlex

from .prototype_module import PrototypeModule

class CommandModule(PrototypeModule):

    _required_keys = ["command"]
    _default_config_dict = {}

    def _run(self):
        try:
            self._split_command
        except AttributeError:
            self._split_command = shlex.shlex(self.config_dict['command'], posix=True)
            self._split_command.whitespace_split = True
            self._split_command = list(self._split_command)

        completed_process = subprocess.run(self._split_command, stdout=subprocess.PIPE)
        return completed_process.stdout.decode("utf-8")

