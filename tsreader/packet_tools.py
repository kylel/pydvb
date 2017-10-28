'''
Tools to decode a 188byte mpeg2ts packet
mostly bit fiddling. should really be done in C
'''

import adaptation_field_tools as aft

SC_NOT_SCRAMBLED  = int('00', 2)
SC_RESERVED       = int('01', 2)
SC_SCRAMBLED_EVEN = int('10', 2)
SC_SCRAMBLED_ODD  = int('11', 2)

AF_RESERVED              = int('00', 2)
AF_PAYLOAD_ONLY          = int('01', 2)
AF_ADAPTATION_FIELD_ONLY = int('10', 2)
AF_AF_AND_PL             = int('11', 2)

def hex_string(data):
    res = ""
    for item in data:
        res += '['+hex(item)+']'
    res += '\n'
    return res

def tei_flag(packet):
    if packet[1] & int('10000000', 2): return True
    return False

def payload_start_flag(packet):
    if packet[1] & int('01000000', 2): return True
    return False

def tp_flag(packet):
    if packet[1] & int('00100000', 2): return True
    return False

def get_pid(packet):
    pid = packet[1] & int('00011111', 2)
    pid = pid << 8
    pid = pid + packet[2]
    return pid

def get_scrambling_control(packet):
    sc = packet[3] & int('11000000', 2)
    sc = sc >> 6
    return sc

def get_adaptation_field(packet):
    af = packet[3] & int('00110000', 2)
    af = af >> 4
    return af

def get_continuity_counter(packet):
    cc = packet[3] & int('00001111', 2)
    return cc

def get_payload(packet):
    offset = 4
    af = get_adaptation_field(packet)
    if af == AF_ADAPTATION_FIELD_ONLY or af == AF_AF_AND_PL:
        offset = offset + 1 + aft.get_length(packet)
    return packet[offset:]

if __name__ == '__main__':
    print 'Testing packet_tools'