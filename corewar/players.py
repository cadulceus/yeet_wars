class Thread(object):
    def __init__(self, pc, xd=0, dx=0, owner=0):
        self.pc = pc
        self.xd = xd
        self.dx = dx
        self.owner = owner

class Player(object):
    def __init__(self):
        self.threads = []