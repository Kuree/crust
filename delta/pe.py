from lassen.sim import gen_pe
from lassen.isa import DATAWIDTH


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

        self._instr = None

    def inputs(self):
        return [self.ports.data0, self.ports.data1, self.ports.bit0,
                self.ports.bit1, self.ports.bit2]

    def outputs(self):
        return [self.ports.out, self.ports.outb]

    def configure_model(self, instr):
        self._instr = instr

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
