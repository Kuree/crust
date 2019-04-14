from peak.pe1 import PE
import peak.pe1.asm as asm
from peak.pe1.mode import Mode
from gemstone.common.core import ConfigurableCore
from gemstone.common.configurable import ConfigurationType
from gemstone.common.mux_with_default import MuxWithDefaultWrapper
import magma
from hwtypes import BitVector, Bit


class PeCore(ConfigurableCore):
    def __init__(self, configure_width: int = 8,
                 configure_data_width: int = 32):
        super().__init__(configure_width, configure_data_width)
        self.add_ports(
            data0=magma.In(magma.Bits[16]),
            data1=magma.In(magma.Bits[16]),
            out=magma.Out(magma.Bits[16]),
            bit0=magma.In(magma.Bits[1]),
            bit1=magma.In(magma.Bits[1]),
            bit2=magma.In(magma.Bits[1]),
            outb=magma.Out(magma.Bits[1]),
            config=magma.In(ConfigurationType(8, 32)),
        )

        # Add some config registers
        self.add_configs(
            dummy_1=32,
            dummy_2=32,
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

        self.pe = PE()
        self.op_map = {
            "add": asm.add(),
            "mult": asm.umult0(),
            "ule": asm.ule(),
        }
        # notice that the peak functional model can't eval the register
        # we have to take care of it by ourselves
        self._reg_values = {"data0": 0, "data1": 0,
                            "bit0": 0, "bit1": 0, "bit2": 0}
        self._reg_mode = {"data0": Mode.BYPASS,
                          "data1": Mode.BYPASS,
                          "bit0": Mode.BYPASS,
                          "bit1": Mode.BYPASS,
                          "bit2": Mode.BYPASS}
        self._instr = None

    def get_config_bitstream(self, instr):
        raise NotImplemented()

    def instruction_type(self):
        raise NotImplemented()

    def inputs(self):
        return [self.ports.data0, self.ports.data1, self.ports.bit0,
                self.ports.bit1, self.ports.bit2]

    def outputs(self):
        return [self.ports.out, self.ports.outb]

    def configure_model(self, instr: str):
        # instr is a string
        # FIXME: fix this re hack
        import re
        tokens = re.split(r"[(),]", instr)
        tokens = [x.strip() for x in tokens]
        op = tokens[0]
        assert op in self.op_map
        self._instr = self.op_map[op]

        # based on the mode, we may want to use reg const or reg mode
        # this will not work for more than 3 inputs
        values = tokens[1:]
        assert len(values) == 2
        for idx, var in enumerate(values):
            if var == "reg":
                self._reg_mode[f"data{idx}"] = Mode.DELAY
            elif "const" in var:
                const_var = int(var.split("_")[-1])
                self._reg_mode[f"data{idx}"] = Mode.CONST
                self._reg_values[f"data{idx}"] = const_var

    def eval_model(self, **kargs):
        # FIXME
        #   currently only 16 bit
        data0 = kargs["data0"] if "data0" in kargs else 0
        data1 = kargs["data1"] if "data1" in kargs else 0

        val0 = data0 if self._reg_mode["data0"] == Mode.BYPASS \
            else self._reg_values["data0"]
        val1 = data1 if self._reg_mode["data1"] == Mode.BYPASS \
            else self._reg_values["data1"]

        assert self._instr is not None
        data = BitVector[16]
        res, res_p, irq = self.pe(self._instr, data(val0), data(val1))

        if self._reg_mode["data0"] == Mode.DELAY:
            self._reg_values["data0"] = data0
        if self._reg_mode["data1"] == Mode.DELAY:
            self._reg_mode["data1"] = data1

        return {"out": int(res), "outb": bool(res_p)}

    def name(self):
        return "PECore"
