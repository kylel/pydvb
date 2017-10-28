'''
    Simple raw data buffer... buff those bytes :)
'''

from threading import Lock, Thread

class Buffer(object):
    def __init__(self, size):
        self.lock = Lock()
        self.data = []
        self.max_size = size
        self.size = 0
        self.linked = False
        self.empty = False

    def write(self, data):
        self.lock.acquire()
        bytes = 0
        try:
            bytes = len(data)
            if self.size + bytes > self.max_size:
                print 'buffer overflow'
                raise Exception
                return 0
            self.size = self.size + bytes
            self.data.append(data)
        finally:
            self.lock.release()
        return bytes

    def read(self):
        data = None
        self.lock.acquire()
        try:
            if self.size <= 0 and not self.linked:
                self.empty = True
                print "Buffer empty"
                return -1
            if len(self.data) <= 0: return None
            data = self.data.pop(0)
            self.size = self.size - len(data)
        finally:
            self.lock.release()
        return data

    def unlink(self):
        self.lock.acquire()
        self.linked = False
        self.lock.release()

    def link(self):
        self.lock.acquire()
        self.linked = True
        self.lock.release()

class BufferReader(Thread):
    def __init__(self, buffer):
        #super(BufferReader, self).__init__()
        Thread.__init__(self)
        self.lock = Lock()
        self.buff = buffer

    def run(self):
        self.halt = False
        while self.keep_going():
            self.loop()

    def _loop(self):
        pass

    def loop(self):
        self.lock.acquire()
        try:
            self._loop()
        finally:
            self.lock.release()

    def keep_going(self):
        self.lock.acquire()
        try:
            return not self.halt
        finally:
            self.lock.release()

    def stop(self):
        self.lock.acquire()
        self.halt = True
        self.lock.release()

if __name__ == '__main__':
    print 'Testing Buffer class'