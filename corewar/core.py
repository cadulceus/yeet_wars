# coding: utf-8

from copy import copy
from struct import unpack

__all__ = ['Core']

class Core(object):
    """The Core itself. An array-like object with a bunch of instructions and
       warriors, and tasks.
    """

    def __init__(self, initial_value=b'\x00', size=8000, core_event_recorder=lambda *args : None):
        self.owner = [-1 for i in range(size)]
        self.size = size
        self.clear(initial_value)
        self.core_event_recorder = core_event_recorder

    def clear(self, byte):
        """Writes the same byte thorough the entire core.
        """
        self.bytes = bytearray(byte)*self.size
        
    def __getitem__(self, address):
        # Python3 seems to have deprecated __getslice__
        if isinstance(address, slice):
            return self.__getslice__(address.start, address.stop)
        return self.bytes[address % self.size]

    def __getslice__(self, start, stop):
        if not start: start = 0
        if not stop: stop = -1
        if start > stop:
            return []
        else:
            return bytearray([self.bytes[(start + i) % self.size] for i in range(stop - start)])

    def __setitem__(self, address, value):
        if isinstance(value, str):
            value = bytes(value, 'UTF-8')

        if isinstance(value, int):
            self.bytes[address % self.size] = value
            self.core_event_recorder(((address % self.size, value)))
        else:
            events = []
            for ctr, byte in enumerate(value):
                if not isinstance(byte, int):
                    converted = ord(byte)
                else:
                    converted = byte
                self.bytes[(address + ctr) % self.size] = byte
                events.append(((address + ctr) % self.size, converted))
            self.core_event_recorder(events)

    def __iter__(self):
        return iter(self.bytes)

    def __len__(self):
        return self.size

    def __repr__(self):
        return "<Core size=%d>" % self.size

if __name__ == "__main__":
    a = Core()