"""This is copied from the garnet for IO with additional eval mode
"""

import magma
from gemstone.common.core import Core, PnRTag


class IO1bit(Core):
    def __init__(self):
        super().__init__()
        TBit = magma.Bits[1]

        self.add_ports(
            glb2io=magma.In(TBit),
            io2glb=magma.Out(TBit),
            io2f_1=magma.Out(TBit),
            f2io_1=magma.In(TBit)
        )
        self.wire(self.ports.glb2io, self.ports.io2f_1)
        self.wire(self.ports.f2io_1, self.ports.io2glb)

    def inputs(self):
        return [self.ports.glb2io, self.ports.f2io_1]

    def outputs(self):
        return [self.ports.io2glb, self.ports.io2f_1]

    def name(self):
        return "io1bit"

    def eval_model(self, **kargs):
        glb2io = kargs["glb2io"] if "glb2io" in kargs else 0
        f2io_1 = kargs["f2io_1"] if "f2io_1" in kargs else 0

        io2glb = f2io_1
        io2f_1 = glb2io

        return {"io2glb": io2glb, "io2f_1": io2f_1}

    def pnr_info(self):
        return PnRTag("i", 0, self.DEFAULT_PRIORITY - 1)


class IO16bit(Core):
    def __init__(self):
        super().__init__()
        TBit = magma.Bits[16]

        self.add_ports(
            glb2io=magma.In(TBit),
            io2glb=magma.Out(TBit),
            io2f_16=magma.Out(TBit),
            f2io_16=magma.In(TBit)
        )
        self.wire(self.ports.glb2io, self.ports.io2f_16)
        self.wire(self.ports.f2io_16, self.ports.io2glb)

    def inputs(self):
        return [self.ports.glb2io, self.ports.f2io_16]

    def outputs(self):
        return [self.ports.io2glb, self.ports.io2f_16]

    def name(self):
        return "io16bit"

    def eval_model(self, **kargs):
        glb2io = kargs["glb2io"] if "glb2io" in kargs else 0
        f2io_16 = kargs["f2io_16"] if "f2io_16" in kargs else 0

        io2glb = f2io_16
        io2f_16 = glb2io

        return {"io2glb": io2glb, "io2f_16": io2f_16}

    def pnr_info(self):
        return PnRTag("I", 0, self.DEFAULT_PRIORITY)
