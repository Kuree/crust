from delta.model import *
from delta.util import create_cgra
import pytest
import lassen.asm as asm
from archipelago import pnr
from karst.core import MemoryInstruction, MemoryMode


@pytest.fixture
def interconnect_route():
    chip_size = 2

    interconnect = create_cgra(chip_size, True, cores_input=None)

    netlist = {"e0": [("I0", "io2f_16"), ("p0", "data0")],
               "e1": [("I1", "io2f_16"), ("p0", "data1")],
               "e2": [("p0", "out"), ("m0", "addr")],
               "e3": [("m0", "data_out"), ("I2", "f2io_16")],
               "e4": [("i0", "io2f_1"), ("m0", "ren")]}
    bus = {"e0": 16, "e1": 16, "e2": 16, "e3": 16, "e4": 1}

    placement, route = pnr(interconnect, (netlist, bus), cwd="temp")

    return interconnect, placement, route


def test_add(interconnect_route):
    interconnect, placement, route_path = interconnect_route
    instruction = asm.add()

    compiler = InterconnectModelCompiler(interconnect)
    compiler.configure_route(route_path)
    x, y = placement["p0"]
    compiler.set_core_instr(x, y, instruction)
    # configure the memory
    data_entries = [(i, i + 42) for i in range(100)]
    mem_instr = MemoryInstruction(MemoryMode.SRAM,
                                  data_entries=data_entries)
    x, y = placement["m0"]
    compiler.set_core_instr(x, y, mem_instr)

    model = compiler.compile()

    # poke values
    path = route_path["e0"][0]
    input_1 = path[0]
    path = route_path["e1"][0]
    input_2 = path[0]
    path = route_path["e4"][0]
    input_3 = path[0]
    path = route_path["e3"][0]
    end = path[-1]

    # set ren to high all the time
    model.set_value(input_3, 1)

    for idx, value in enumerate(range(10)):
        model.set_value(input_1, value)
        model.set_value(input_2, value)
        model.eval()
        if idx > 0:
            assert model.get_value(end) == value + value + 42 - 2
