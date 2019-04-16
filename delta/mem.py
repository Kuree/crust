from karst.core import MemoryCore as KarstCore, MemoryInstruction
from .dummy_core import DummyCore
import magma


class MemoryCore(DummyCore):
    def __init__(self, memory_size: int = 1024, configure_width: int = 8,
                 configure_data_width: int = 32):
        super().__init__(configure_width, configure_data_width)
        self.add_ports(
            data_in=magma.In(magma.Bits[16]),
            data_out=magma.Out(magma.Bits[16]),
            wen=magma.In(magma.Bits[1]),
            valid=magma.Out(magma.Bits[1])
        )

        self.core = KarstCore(memory_size)
        self.memory_size = memory_size

        self._data_out_value = 0

    def inputs(self):
        return [self.ports.data_in, self.ports.wen]

    def outputs(self):
        return [self.ports.data_out, self.ports.valid]

    def configure_model(self, instr: MemoryInstruction):
        self.core.configure(instr)

    def eval_model(self, **kargs):
        return self.core.eval(**kargs)

    def name(self):
        return "MEMCore"
