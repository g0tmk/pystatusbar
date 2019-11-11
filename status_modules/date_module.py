import time

from .prototype_module import PrototypeModule

class DateModule(PrototypeModule):

    _required_keys = ["template"]
    _default_config_dict = {
        "template": "%b %d %y",
    }

    def _run(self):
        return time.strftime(self.config_dict['template'])

