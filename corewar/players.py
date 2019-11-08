from struct import pack, unpack

class Thread(object):
    def __init__(self, pc, xd=0, dx=0, owner=0, thread_id=-1):
        self.pc = pc
        self.id = thread_id
        self._xd = unpack('>I', xd)[0] if isinstance(xd, (str, bytearray)) else xd
        self._dx = unpack('>I', dx)[0] if isinstance(dx, (str, bytearray)) else dx
        self.owner = owner
        # blame represents the player id of whoever
        self.xd_blame = owner
        self.dx_blame = owner
        
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
        return "ID: {} PC: {} Owner: {} XD: {} DX: {}".format(self.id, self.pc, self.owner, str(self.xd_bytes).encode("hex"), str(self.dx_bytes).encode("hex") )
        
    

class Player(object):
    def __init__(self, name, player_id, token, score=0, color="#0000FF"):
        self.threads = []
        self.name = name
        self.id = player_id
        self.token = token
        self.score = score
        self.color = color
        
    def __str__(self):
        return "{} ({})".format(self.name, self.id)