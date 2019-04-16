from delta.model import *
from delta.util import create_cgra
import pytest
import tempfile
from archipelago import pnr


@pytest.fixture
def interconnect_route():
    chip_size = 2

    interconnect = create_cgra(chip_size, True, cores_input=None)

    netlist = {"e0": [("I0", "io2f_16"), ("p0", "data0")],
               "e1": [("p0", "out"), ("I1", "f2io_16")]}
    bus = {"e0": 16, "e1": 16}

    with tempfile.TemporaryDirectory() as tempdir:
        placement, route = pnr(interconnect, (netlist, bus), cwd=tempdir)

    # two paths
    route_path = [route["e0"][0], route["e1"][0]]

    return interconnect, placement, route_path


@pytest.mark.parametrize("magic_value", [42])
def test_add(interconnect_route, magic_value):
    interconnect, placement, route_path = interconnect_route

    compiler = InterconnectModelCompiler(interconnect)
    compiler.configure_route(route_path)
    x, y = placement["p0"]
    compiler.set_core_instr(x, y, f"add(wire, const_{magic_value}")
    # no instruction as we are using dummy
    model = compiler.compile()

    # poke values
    first_path, second_path = route_path
    start = first_path[0]
    end = second_path[-1]

    num_data_points = 10
    values = []
    for i in range(num_data_points):
        values.append(i + 1)
    for idx, value in enumerate(values):
        model.set_value(start, value)
        model.eval()
        assert model.get_value(end) == value + magic_value
