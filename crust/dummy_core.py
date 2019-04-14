from gemstone.common.core import ConfigurableCore
from gemstone.common.mux_with_default import MuxWithDefaultWrapper
import magma
from gemstone.common.configurable import ConfigurationType


class DummyCore(ConfigurableCore):
    def __init__(self, configure_width: int = 8,
                 configure_data_width: int = 32):
        super().__init__(configure_width, configure_data_width)

        # Add some config registers
        self.add_configs(
            dummy_1=32,
            dummy_2=32,
        )

        self.add_ports(
            config=magma.In(ConfigurationType(8, 32))
        )

        # Create mux allow for reading of config regs
        num_mux_inputs = len(self.registers.values())
        self.read_data_mux = MuxWithDefaultWrapper(num_mux_inputs, 32, 8, 0)
        # Connect config_addr to mux select
        self.wire(self.read_data_mux.ports.S, self.ports.config.config_addr)
        # Connect config_read to mux enable
        self.wire(self.read_data_mux.ports.EN[0], self.ports.config.read[0])
        self.wire(self.read_data_mux.ports.O, self.ports.read_config_data)
        for i, reg in enumerate(self.registers.values()):
            reg.set_addr(i)
            reg.set_addr_width(8)
            reg.set_data_width(32)
            # wire output to read_data_mux inputs
            self.wire(reg.ports.O, self.read_data_mux.ports.I[i])
            # Wire config addr and data to each register
            self.wire(self.ports.config.config_addr, reg.ports.config_addr)
            self.wire(self.ports.config.config_data, reg.ports.config_data)
            # Wire config write to each reg's write port
            self.wire(self.ports.config.write[0], reg.ports.config_en)
            self.wire(self.ports.reset, reg.ports.reset)

        self._instr = None

    def get_config_bitstream(self, instr):
        raise NotImplemented()

    def instruction_type(self):
        raise NotImplemented()
