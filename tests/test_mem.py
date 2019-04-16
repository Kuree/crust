from delta.model import *
from karst.core import MemoryInstruction, MemoryMode
from archipelago import pnr
import pytest
from delta.util import create_cgra
import tempfile


@pytest.fixture
def interconnect_route():
    chip_size = 2

    interconnect = create_cgra(chip_size, True, cores_input=None)

    netlist = {"e0": [("I0", "io2f_16"), ("M0", "data_in")],
               "e1": [("M0", "data_out"), ("I1", "f2io_16")],
               "e2": [("i0", "io2f_1"), ("M0", "wen")]}
    bus = {"e0": 16, "e1": 16, "e2": 1}

    with tempfile.TemporaryDirectory() as tempdir:
        placement, route = pnr(interconnect, (netlist, bus), cwd=tempdir)

    # two paths
    route_path = [route["e0"][0], route["e1"][0], route["e2"][0]]

    return interconnect, placement, route_path


@pytest.mark.parametrize("depth", [10])
def test_add(interconnect_route, depth):
    interconnect, placement, route_path = interconnect_route

    compiler = InterconnectModelCompiler(interconnect)
    compiler.configure_route(route_path)
    x, y = placement["M0"]
    instr = MemoryInstruction(MemoryMode.RowBuffer, {"depth": depth})
    compiler.set_core_instr(x, y, instr)
    # no instruction as we are using dummy
    model = compiler.compile()

    # poke values
    first_path, second_path, third_path = route_path
    start = first_path[0]
    wen = third_path[0]
    end = second_path[-1]

    num_data_points = depth * 2
    values = []
    for i in range(num_data_points):
        values.append(i + 1)

    for idx, value in enumerate(values):
        model.set_value(start, value)
        model.set_value(wen, 1)
        model.eval()
        if idx >= depth:
            assert model.get_value(end) == values[idx - depth]
