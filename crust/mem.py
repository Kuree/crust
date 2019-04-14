from karst.basic import define_row_buffer
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

        self.row_buffer = define_row_buffer()
        self.memory_size = memory_size

        self._data_out_value = 0

    def inputs(self):
        return [self.ports.data_in, self.ports.wen]

    def outputs(self):
        return [self.ports.data_out, self.ports.valid]

    def configure_model(self, instr: str):
        depth = int(instr)
        self.row_buffer.configure(memory_size=self.memory_size,
                                  depth=depth)

    def eval_model(self, **kargs):
        data_in = kargs["data_in"] if "data_in" in kargs else 0
        wen = kargs["wen"] if "wen" in kargs else 0

        self.row_buffer.wen = 1
        if wen:
            self.row_buffer.data_in = data_in
            data_out = self.row_buffer.enqueue()
            self._data_out_value = data_out
        else:
            # latch out the last data
            data_out = self._data_out_value
        valid = self.row_buffer.valid.eval()

        return {"data_out": data_out, "valid": valid}

    def name(self):
        return "MEMCore"
