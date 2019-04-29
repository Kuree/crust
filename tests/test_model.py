from delta.model import *
from gemstone.common.dummy_core_magma import DummyCore
import pytest
from delta.vcd import *
import tempfile
import os
from delta.util import *
from archipelago import pnr


@pytest.fixture
def interconnect_route():
    chip_size = 2

    # creates all the cores here
    # we don't want duplicated cores when snapping into different interconnect
    # graphs
    cores = {}
    for x in range(0, chip_size + 2):
        for y in range(0, chip_size + 2):
            cores[(x, y)] = IO16bit()
    for x in range(1, 1 + chip_size):
        for y in range(1, 1 + chip_size):
            cores[(x, y)] = DummyCore()
    # corners
    for x, y in [(0, 0), (0, chip_size + 1), (chip_size + 1, 0),
                 (chip_size + 1, chip_size + 1)]:
        cores[(x, y)] = None

    interconnect = create_cgra(chip_size, True, cores_input=cores)

    netlist = {"e0": [("I0", "io2f_16"), ("r0", "reg")],
               "e1": [("r0", "reg"), ("D0", "data_in_16b")],
               "e2": [("D0", "data_out_16b"), ("I1", "f2io_16")]}
    bus = {"e0": 16, "e1": 16, "e2": 16}

    with tempfile.TemporaryDirectory() as tempdir:
        _, route = pnr(interconnect, (netlist, bus), cwd=tempdir)

    # two paths
    route_path = [route["e0"][0], route["e1"][0], route["e2"][0]]

    return interconnect, route_path


def test_simulation(interconnect_route):
    interconnect, route_path = interconnect_route

    compiler = InterconnectModelCompiler(interconnect)
    compiler.configure_route(route_path)
    # no instruction as we are using dummy
    model = compiler.compile()

    # poke values
    first_path, _, second_path = route_path
    start = first_path[0]
    end = second_path[-1]

    num_data_points = 10
    values = []
    for i in range(num_data_points):
        values.append(i + 1)
    for idx, value in enumerate(values):
        model.set_value(start, value)
        model.eval()
        if idx > 0:
            # one pipeline register
            assert model.get_value(end) == values[idx - 1]


def test_vcd(interconnect_route):
    interconnect, route_path = interconnect_route

    compiler = InterconnectModelCompiler(interconnect)
    compiler.configure_route(route_path)
    # no instruction as we are using dummy
    model = compiler.compile()

    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, "test.vcd")
        with ModelVCD(model, filename) as vcd:
            model.attach_vcd(vcd)

            # poke values
            first_path, _, second_path = route_path
            start = first_path[0]
            end = second_path[-1]

            num_data_points = 10
            values = []
            for i in range(num_data_points):
                values.append(i + 1)
            for idx, value in enumerate(values):
                model.set_value(start, value)
                model.eval()
                if idx > 0:
                    # one pipeline register
                    assert model.get_value(end) == values[idx - 1]
        assert os.path.getsize(filename) > 10
