from delta.model import *
from delta.util import create_cgra
import pytest
import tempfile
from archipelago import pnr
import lassen.mode as mode
from lassen.isa import gen_alu_type
from lassen.asm import inst
from lassen.family import gen_pe_type_family
from hwtypes import BitVector


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


@pytest.fixture
def add_instr(request):
    family = gen_pe_type_family(BitVector.get_family())
    mode_type = mode.gen_mode_type(family)
    magic_value = request.param

    # based on the mode, we may want to use reg const or reg mode
    # this will not work for more than 3 inputs

    reg_modes = {"ra_mode": mode_type.BYPASS, "rb_mode": mode_type.CONST}
    reg_values = {"ra_const": 0, "rb_const": magic_value}

    alu_types = gen_alu_type(family)
    alu_type = alu_types.Add
    kargs = {}
    kargs.update(reg_modes)
    kargs.update(reg_values)
    return inst(alu_type, **kargs), magic_value


@pytest.mark.parametrize("add_instr", [42], indirect=["add_instr"])
def test_add(interconnect_route, add_instr):
    interconnect, placement, route_path = interconnect_route
    instruction, magic_value = add_instr

    compiler = InterconnectModelCompiler(interconnect)
    compiler.configure_route(route_path)
    x, y = placement["p0"]
    compiler.set_core_instr(x, y, instruction)
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
