from canal.interconnect import Interconnect
from canal.util import create_uniform_interconnect, SwitchBoxType, IOSide
from canal.cyclone import SwitchBoxSide, SwitchBoxIO
from .io import IO16bit, IO1bit
from .mem import MemoryCore
from .pe import PeCore


def create_cgra(chip_size: int, add_io: bool = False, cores_input=None):
    # currently only add 16bit io cores
    num_tracks = 2
    reg_mode = True
    addr_width = 8
    data_width = 32
    bit_widths = [1, 16]
    tile_id_width = 16
    track_length = 1
    margin = 0 if not add_io else 1
    chip_size += 2 * margin
    # recalculate the margin
    # creates all the cores here
    # we don't want duplicated cores when snapping into different interconnect
    # graphs
    if cores_input is None:
        cores_input = {}
    cores = {}
    for x in range(chip_size):
        for y in range(chip_size):
            if (x, y) in cores_input:
                # allow it to override
                cores[(x, y)] = cores_input[(x, y)]
                continue
            # empty corner
            if x in range(margin) and y in range(margin):
                core = None
            elif x in range(margin) and y in range(chip_size - margin,
                                                   chip_size):
                core = None
            elif x in range(chip_size - margin,
                            chip_size) and y in range(margin):
                core = None
            elif x in range(chip_size - margin,
                            chip_size) and y in range(chip_size - margin,
                                                      chip_size):
                core = None
            elif x in range(margin) \
                    or x in range(chip_size - margin, chip_size) \
                    or y in range(margin) \
                    or y in range(chip_size - margin, chip_size):
                if x == margin or y == margin:
                    core = IO16bit()
                else:
                    core = IO1bit()
            else:
                core = MemoryCore(1024) if ((x - margin) % 2 == 1) else \
                    PeCore()
            cores[(x, y)] = core

    def create_core(xx: int, yy: int):
        return cores[(xx, yy)]

    # specify input and output port connections
    inputs = ["data0", "data1", "bit0", "bit1", "bit2", "data_in",
              "addr_in", "flush", "ren_in", "wen_in", "data_in_16b", "wen",
              "ren"]
    outputs = ["out", "outb", "data_out", "data_out_16b"]
    # this is slightly different from the chip we tape out
    # here we connect input to every SB_IN and output to every SB_OUT
    port_conns = {}
    in_conn = []
    out_conn = []
    for side in SwitchBoxSide:
        in_conn.append((side, SwitchBoxIO.SB_IN))
        out_conn.append((side, SwitchBoxIO.SB_OUT))
    for input_port in inputs:
        port_conns[input_port] = in_conn
    for output_port in outputs:
        port_conns[output_port] = out_conn
    pipeline_regs = []
    for track in range(num_tracks):
        for side in SwitchBoxSide:
            pipeline_regs.append((track, side))
    # if reg mode is off, reset to empty
    if not reg_mode:
        pipeline_regs = []
    ics = {}

    sides = IOSide.North | IOSide.East | IOSide.South | IOSide.West

    io_in = {"f2io_1": [1], "f2io_16": [0]}
    io_out = {"io2f_1": [1], "io2f_16": [0]}
    for bit_width in bit_widths:
        if add_io:
            io_conn = {"in": io_in, "out": io_out}
        else:
            io_conn = None
        ic = create_uniform_interconnect(chip_size, chip_size, bit_width,
                                         create_core,
                                         port_conns,
                                         {track_length: num_tracks},
                                         SwitchBoxType.Disjoint,
                                         pipeline_regs,
                                         io_sides=sides,
                                         io_conn=io_conn)
        ics[bit_width] = ic

    interconnect = Interconnect(ics, addr_width, data_width, tile_id_width)

    return interconnect
