from struct import pack, unpack
import binascii

class Thread(object):
    def __init__(self, pc, xd=0, dx=0, owner=0, thread_id=-1):
        self.pc = pc
        self.id = thread_id
        self._xd = self.reg_to_int(xd)
        self._dx = self.reg_to_int(dx)
        self.owner = owner
        # blame represents the player id of whoever
        self.xd_blame = owner
        self.dx_blame = owner

    def reg_to_int(self, reg):
        match reg:
            case bytes() | bytearray():
                return unpack('>I', reg)[0]
            case str():
                return unpack('>I', bytes(reg, 'UTF-8'))[0]
            case int():
                return reg
        
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
        self._xd = self.reg_to_int(val)
    
    @dx.setter
    def dx(self, val):
        self._dx = self.reg_to_int(val)
        
    def __str__(self):
        return "ID: {} PC: {} Owner: {} XD: {} DX: {}".format(self.id, self.pc, self.owner, binascii.hexlify(self.xd_bytes), binascii.hexlify(self.dx_bytes))
        
    

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