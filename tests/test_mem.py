from crust.model import *
from crust.mem import MemoryCore
from canal.util import *
from canal.cyclone import *
import pytest


@pytest.fixture
def interconnect_route():
    addr_width = 8
    data_width = 32
    bit_widths = [1, 16]
    chip_size = 2
    num_tracks = 2

    tile_id_width = 16
    track_length = 1

    # creates all the cores here
    # we don't want duplicated cores when snapping into different interconnect
    # graphs
    cores = {}
    for x in range(chip_size):
        for y in range(chip_size):
            cores[(x, y)] = MemoryCore()

    def create_core(xx: int, yy: int):
        return cores[(xx, yy)]

    in_conn = []
    out_conn = []
    for side in SwitchBoxSide:
        in_conn.append((side, SwitchBoxIO.SB_IN))
        out_conn.append((side, SwitchBoxIO.SB_OUT))

    ics = {}
    ports = {"data_in": in_conn, "wen": in_conn, "data_out": out_conn,
             "valid": in_conn}
    for bit_width in bit_widths:
        ic = create_uniform_interconnect(chip_size, chip_size, bit_width,
                                         create_core,
                                         ports,
                                         {track_length: num_tracks},
                                         SwitchBoxType.Disjoint)
        ics[bit_width] = ic

    interconnect = Interconnect(ics, addr_width, data_width, tile_id_width,
                                lift_ports=True)

    # manual route
    # I wish I can use pycyclone here to do the automatic routing
    graph = interconnect.get_graph(16)
    first_path = []
    start_node = graph.get_sb(0, 0, SwitchBoxSide.WEST,
                              0, SwitchBoxIO.SB_IN)
    next_node = graph.get_port(0, 0, "data_in")
    first_path.append(start_node)
    first_path.append(next_node)

    second_path = []
    port_out = graph.get_port(0, 0, "data_out")
    second_path.append(port_out)
    # route to a sb node
    next_node = graph.get_sb(0, 0, SwitchBoxSide.EAST, 0, SwitchBoxIO.SB_OUT)
    second_path.append(next_node)
    # append a register as well
    nodes = list(next_node)
    assert len(nodes) == 1
    next_node = nodes[0]
    second_path.append(next_node)
    next_node = list(next_node)[0]
    second_path.append(next_node)
    next_node = graph.get_sb(1, 0, SwitchBoxSide.EAST, 0, SwitchBoxIO.SB_OUT)
    second_path.append(next_node)

    third_path = []
    graph = interconnect.get_graph(1)
    start_node = graph.get_sb(0, 0, SwitchBoxSide.NORTH,
                              0, SwitchBoxIO.SB_IN)
    next_node = graph.get_port(0, 0, "wen")
    third_path.append(start_node)
    third_path.append(next_node)

    # three paths
    route_path = [first_path, second_path, third_path]

    return interconnect, route_path


@pytest.mark.parametrize("depth", [10])
def test_add(interconnect_route, depth):
    interconnect, route_path = interconnect_route

    compiler = InterconnectModelCompiler(interconnect)
    compiler.configure_route(route_path)
    compiler.set_core_instr(0, 0, depth)
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
