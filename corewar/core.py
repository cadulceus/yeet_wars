# coding: utf-8

from copy import copy
from struct import unpack

__all__ = ['Core']

class Core(object):
    """The Core itself. An array-like object with a bunch of instructions and
       warriors, and tasks.
    """

    def __init__(self, initial_value='\x00', size=8000, event_recorder=lambda *args : None):
        self.owner = [-1 for i in range(size)]
        self.size = size
        self.clear(initial_value)
        self.event_recorder = event_recorder

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
            return bytearray([self.bytes[(start + i) % self.size] for i in range(stop - start)])

    def __setitem__(self, address, value):
        if isinstance(value, (int, long)):
            self.bytes[address % self.size] = value
            self.event_recorder(((address % self.size, value)))
        else:
            events = []
            for ctr, byte in enumerate(value):
                if not isinstance(byte, (int, long)):
                    converted = ord(byte)
                else:
                    converted = byte
                self.bytes[(address + ctr) % self.size] = byte
                events.append(((address + ctr) % self.size, converted))
            self.event_recorder(events)

    def __iter__(self):
        return iter(self.bytes)

    def __len__(self):
        return self.size

    def __repr__(self):
        return "<Core size=%d>" % self.size

if __name__ == "__main__":
    a = Core()