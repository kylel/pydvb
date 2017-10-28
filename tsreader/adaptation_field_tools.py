'''
Tools for decoding the adaptation field of a mpeg2ts packet.
mostly bit fiddling. should be done in C for performance reasons but this should work for now
'''

class Pcr:
    def __init__(self):
        self.base      = 0
        self.reserved  = 0
        self.extension = 0

    def parse(cls, data):
        pcr = Pcr()
        pcr.base = (data[0] << 8) + data[1]
        pcr.base = (pcr.base << 8) + data[2]
        pcr.base = (pcr.base << 8) + data[3]
        pcr.base = pcr.base << 1
        last_byte = (data[4]>>7) & int('00000001', 2)
        pcr.base = pcr.base + last_byte

        pcr.extension = data[4] & int('00000001',2)
        pcr.extension = (pcr.extension << 8) + data[5]

        return pcr

    parse = classmethod(parse)

    def __str__(self):
        return "base[" + str(self.base) + "], extension[" + str(self.extension) + "]"

    def to_micro_seconds(self):
        base = (1.0/90000.0) * self.base
        ext  = (1.0/27000000.0) * self.extension
        return (base + ext) * 1000000

def get_length(packet):
    return packet[4]

def discontinuity_flag(packet):
    if packet[5] & int('10000000', 2): return True
    return False

def random_access_flag(packet):
    if packet[5] & int('01000000', 2): return True
    return False

def elementary_stream_priority_flag(packet):
    if packet[5] & int('00100000', 2): return True
    return False

def pcr_flag(packet):
    if packet[5] & int('00010000', 2): return True
    return False

def opcr_flag(packet):
    if packet[5] & int('00001000', 2): return True
    return False

def splicing_point_flag(packet):
    if packet[5] & int('00000100', 2): return True
    return False

def private_data_flag(packet):
    if packet[5] & int('00000010', 2): return True
    return False

def extension_flag(packet):
    if packet[5] & int('00000001', 2): return True
    return False

def get_pcr(packet):
    pcr_data = packet[6:12]
    pcr = Pcr.parse(pcr_data)
    return pcr

def get_opcr(packet):
    pcr_data = packet[12:18]
    opcr = Pcr.parse(pcr_data)
    return opcr

def get_splice_countdown(packet):
    return int(packet[18]) #can be negative

if __name__ == '__main__':
    print 'Testing adaptation_field_tools'