# coding: utf-8

from copy import copy

__all__ = ['Core']

class Core(object):
    """The Core itself. An array-like object with a bunch of instructions and
       warriors, and tasks.
    """

    def __init__(self, initial_value='\x00', size=8000):
        self.owner = [-1 for i in range(size)]
        self.size = size
        self.clear(initial_value)

    def clear(self, byte):
        """Writes the same byte thorough the entire core.
        """
        self.bytes = bytearray(byte)*self.size
        
    def __getitem__(self, address):
        return self.bytes[address % self.size]

    def __getslice__(self, start, stop):
        if start > stop:
            return []
        else:
            return [self.bytes[start + i % self.size] for i in range(stop - start)]

    def __setitem__(self, address, value):
        if len(value) == 1:
            self.bytes[address % self.size] = value
        else:
            for ctr, byte in enumerate(value):
                self.bytes[address + ctr % self.size] = byte

    def __iter__(self):
        return iter(self.bytes)

    def __len__(self):
        return self.size

    def __repr__(self):
        return "<Core size=%d>" % self.size

if __name__ == "__main__":
    a = Core()