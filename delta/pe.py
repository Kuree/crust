from lassen.sim import gen_pe
from lassen.isa import DATAWIDTH, gen_alu_type, gen_inst_type
from lassen.asm import inst
from lassen.family import gen_pe_type_family
import lassen.mode as mode
from .dummy_core import DummyCore
import magma
from hwtypes import BitVector


class PeCore(DummyCore):
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
        )

        self.pe = gen_pe(BitVector.get_family())()
        self.__family = gen_pe_type_family(BitVector.get_family())
        alu_type = gen_alu_type(self.__family)
        self.op_map = {
            "add": alu_type.Add,
            "mult": alu_type.Mult0,
        }
        self._instr = None

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

        mode_type = mode.gen_mode_type(self.__family)

        # based on the mode, we may want to use reg const or reg mode
        # this will not work for more than 3 inputs
        values = tokens[1:]
        reg_modes = {"ra_mode": mode_type.BYPASS, "rb_mode": mode_type.BYPASS}
        reg_values = {"ra_const": 0, "rb_const": 0}
        assert len(values) == 2
        for idx, var in enumerate(values):
            if var == "reg":
                if idx == 0:
                    reg_modes["ra_mode"] = mode_type.VALID
                else:
                    reg_modes["rb_mode"] = mode_type.VALID
            elif "const" in var:
                const_var = int(var.split("_")[-1])
                if idx == 0:
                    reg_values["ra_const"] = const_var
                    reg_modes["ra_mode"] = mode_type.CONST
                else:
                    reg_values["rb_const"] = const_var
                    reg_modes["rb_mode"] = mode_type.CONST
        alu_type = self.op_map[op]
        kargs = {}
        kargs.update(reg_modes)
        kargs.update(reg_values)
        self._instr = inst(alu_type, **kargs)

    def eval_model(self, **kargs):
        # FIXME
        #   currently only 16 bit
        data0 = kargs["data0"] if "data0" in kargs else 0
        data1 = kargs["data1"] if "data1" in kargs else 0

        assert self._instr is not None
        data = BitVector[DATAWIDTH]
        res, res_p, irq = self.pe(self._instr, data(data0), data(data1))

        return {"out": int(res), "outb": bool(res_p)}

    def name(self):
        return "PECore"
