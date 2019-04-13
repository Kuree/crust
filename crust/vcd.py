from vcd import VCDWriter
from vcd.writer import Variable
from typing import Dict
from canal.cyclone import Node


class ModelVCD:
    def __init__(self, model, filename):
        self.nodes: Dict[Node, Variable] = {}
        self.model = model
        self._fd = open(filename, "w+")
        self._vcd = VCDWriter(self._fd)
        self._timestamp = 0
        self.__top = "Top"
        # create variables in the model
        for node in model.nodes:
            tile = f"{self.__top}.TILE_X{node.x}Y_{node.y}"
            node_name = str(node)
            var = self._vcd.register_var(tile, node_name, "integer",
                                         size=node.width, init=0)
            self.nodes[node] = var
        self.clk = self._vcd.register_var(self.__top, "clk", "integer", size=1,
                                          init=False)
        self.clk_val = 0

    def eval(self, tick=False):
        self._timestamp += 1
        if tick:
            self.clk_val ^= 1
        self._vcd.change(self.clk, self._timestamp, self.clk_val)

        for node, var in self.nodes.items():
            value = self.model.get_value(node)
            self._vcd.change(var, self._timestamp, value)
        if tick:
            self._timestamp += 1
            self.clk_val ^= 1
            self._vcd.change(self.clk, self._timestamp, self.clk_val)

    def close(self):
        self._vcd.close()
        self._fd.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
