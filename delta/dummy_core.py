from gemstone.generator.port_reference import PortReference
from gemstone.common.core import Core


class DummyCore(Core):
    DEFAULT_PRIORITY = 20

    def __init__(self, configure_width: int = 8,
                 configure_data_width: int = 32):
        super().__init__()
        self._instr = None
        self.config_width = configure_width
        self.configure_data_width = configure_data_width

        self.ports = {}

    def add_ports(self, **karg):
        for port_name, port in karg.items():
            self.ports[port_name] = PortReference(self, port_name, port)

    def get_config_bitstream(self, instr):
        raise NotImplemented()

    def instruction_type(self):
        raise NotImplemented()

    def inputs(self):
        return []

    def outputs(self):
        return []

    def name(self):
        return "DummyCore"
