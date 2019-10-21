from struct import pack, unpack

class Thread(object):
    def __init__(self, pc, xd=0, dx=0, owner=0):
        self.pc = pc
        self._xd = unpack('>I', xd)[0] if isinstance(xd, (str, bytearray)) else xd
        self._dx = unpack('>I', dx)[0] if isinstance(dx, (str, bytearray)) else dx
        self.owner = owner
        
    @property
    def xd_bytes(self):
        return pack('>I', self._xd)

    @property
    def dx_bytes(self):
        return pack('>I', self._dx)

    @property
    def xd(self):
        return self._xd

    @property
    def dx(self):
        return self._dx
    
    @xd.setter
    def xd(self, val):
        self._xd = unpack('>I', val)[0] if isinstance(val, (str, bytearray)) else val
    
    @dx.setter
    def dx(self, val):
        self._dx = unpack('>I', val)[0] if isinstance(val, (str, bytearray)) else val
        
    def __str__(self):
        return "PC: {}, Owner: {}\nXD: {} DX: {}".format(self.pc, self.owner, list(self.xd_bytes), list(self.dx_bytes))
        
    

class Player(object):
    def __init__(self):
        self.threads = []