from mpeg2psi import descriptors
from mpeg2psi.descriptors import Descriptor

POL_LINEAR_HORIZONTAL = int('00', 2)
POL_LINEAR_VERTICAL   = int('01', 2)
POL_CIRCULAR_LEFT     = int('10', 2)
POL_LINEAR_RIGHT      = int('11', 2)

POL_STRINGS = {POL_LINEAR_HORIZONTAL:'horizontal',
               POL_LINEAR_VERTICAL  :'vertical',
               POL_CIRCULAR_LEFT    :'left',
               POL_LINEAR_RIGHT     :'right'}

MOD_SYS_DVBS  = int('0', 2)
MOD_SYS_DVBS2 = int('1', 2)

MOD_SYS_STRINGS = {MOD_SYS_DVBS :'DVB-S',
                   MOD_SYS_DVBS2:'DVB-S2'}

MOD_TYPE_AUTO  = int('00', 2)
MOD_TYPE_QPSK  = int('01', 2)
MOD_TYPE_8PSK  = int('10', 2)
MOD_TYPE_16QAM = int('11', 2)

MOD_TYPE_STRINGS = {MOD_TYPE_AUTO :'Auto',
                    MOD_TYPE_QPSK :'QPSK',
                    MOD_TYPE_8PSK :'8PSK',
                    MOD_TYPE_16QAM:'16QAM'}

ROLL_OFF = {int('00', 2): 0.35,
            int('01', 2): 0.25,
            int('10', 2): 0.20}

FEC_UNDEFINED = int('0000', 2)
FEC_1_2       = int('0001', 2)
FEC_2_3       = int('0010', 2)
FEC_3_4       = int('0011', 2)
FEC_5_6       = int('0100', 2)
FEC_7_8       = int('0101', 2)
FEC_8_9       = int('0110', 2)
FEC_3_5       = int('0111', 2)
FEC_4_5       = int('1000', 2)
FEC_9_10      = int('1001', 2)
FEC_NONE      = int('1111', 2)

FEC_STRINGS = {FEC_UNDEFINED:'undefined',
               FEC_1_2      :'1/2',
               FEC_2_3      :'2/3',
               FEC_3_4      :'3/4',
               FEC_5_6      :'5/6',
               FEC_7_8      :'7/8',
               FEC_8_9      :'8/9',
               FEC_3_5      :'3/5',
               FEC_4_5      :'4/5',
               FEC_9_10     :'9/10',
               FEC_NONE     :'None'}

SERVICE_TYPE_STRINGS = {0x01: 'DIGITAL_TV',
                        0x02: 'DIGITAL_RADIO',
                        0x03: 'TELETEXT',
                        0x04: 'NVOD_reference',
                        0x05: 'NVOD_time-shifted',
                        0x06: 'mosaic',
                        0x07: 'RESERVED',
                        0x08: 'RESERVED',
                        0x09: 'RESERVED',
                        0x0A: 'advanced_codec_digital_radio_sound',
                        0x0B: 'advanced_codec_mosaic',
                        0x0C: 'data_broadcast_service',
                        0x0D: 'reserved for Common Interface Usage',
                        0x0E: 'RCS Map',
                        0x0F: 'RCS FLS',
                        0x10: 'DVB MHP service',
                        0x11: 'MPEG-2 HD digital television service',
                        0x12: 'RESERVED',
                        0x13: 'RESERVED',
                        0x14: 'RESERVED',
                        0x15: 'RESERVED',
                        0x16: 'advanced_codec_SD_digital_television',
                        0x17: 'advanced_codec_SD_NVOD_time-shifted',
                        0x18: 'advanced_codec_SD_NVOD_reference',
                        0x19: 'advanced_codec_HD_digital_television',
                        0x1A: 'advanced_codec_HD_NVOD_time-shifted',
                        0x1B: 'advanced_codec_HD_NVOD_reference'}


BEHAVIOUR_STRINGS = {0:'DEFAULT',
                     1:'ALLOW FTA',
                     2:'ALLOW FTA WHEN SMART CARD INSERTED',
                     3:'ALLOW FTA WHEN VALIDATED SMART CARD INSERTED',
                     4:'ALLOW ALL'}


LINKAGE_TYPE_STRINGS = {0x00:'RESERVED',
                        0x01:'information service',
                        0x02:'EPG service',
                        0x03:'CA replacement service',
                        0x04:'TS containing complete Network/Bouquet SI',
                        0x05:'service replacement service',
                        0x06:'data broadcast service',
                        0x07:'RCS Map',
                        0x08:'mobile hand-over',
                        0x09:'System Software Update Service',
                        0x0A:'TS containing SSU BAT or NIT',
                        0x0B:'IP/MAC Notification Service',
                        0x0C:'TS containing INT BAT or NIT'}

HANDOVER_TYPE_STRINGS = {0x00:'RESERVED',
                         0x01:'DVB hand-over to an identical service in a neighbouring country',
                         0x02:'DVB hand-over to a local variation of the same service',
                         0x03:'DVB hand-over to an associated service',
                         0x04:'RESERVED'}

ORIGIN_TYPE_STRINGS = {0x00:'NIT',
                       0x01:'SDT'}

def get_descriptors(data):
    return descriptors.get_descriptors(data)

def bcd2int(data):
    res = 0
    ln = len(data)
    index = 0
    while index < ln:
        res *= 10
        res += (data[index] & int('11110000', 2)) >> 4
        res *= 10
        res += data[index] & int('00001111', 2)
        index += 1
    return res

class LinkageDescriptor(Descriptor):
    tag = 0x4a
    def __init__(self, data):
        self.transport_stream_id = None
        self.original_network_id = None
        self.service_id = None
        self.linkage_type = None
        super(LinkageDescriptor, self).__init__(data)
    
    def parse(self, data):
        super(LinkageDescriptor, self).parse(data)
        self.transport_stream_id = (data[2] << 8) + data[3]
        self.original_network_id = (data[4] << 8) + data[5]
        self.service_id = (data[6] << 8) + data[7]
        self.linkage_type = data[8]
        
        if self.linkage_type != 0x08:
            self.private_data = data[9:self.length]
        else:
            flags = data[9]
            offset = 0
            self.hand_over_type = flags & int('11110000', 2)
            self.origin_type    = flags & int('00000001', 2)
            if self.hand_over_type >= 1 and self.hand_over_type <= 3:
                self.network_id = (data[10] << 8) + data[11]
                offset += 2
            if self.origin_type == 0:
                self.initial_service_id = (data[10 + offset] << 8) + data[11 + offset]
                offset += 2
            self.private_data = data[10+offset:self.length]
                
    def _get_handover_string(self):
        res = '\tMobile Handover:\n'
        handover_type = 'RESERVED'
        if self.hando_over_type in HANDOVER_TYPE_STRINGS:
            handover_type = HANDOVER_TYPE_STRINGS[self.hand_over_type]
        res += '\t\tHandover Type = [%s]\n'%(handover_type)
        res += '\t\tOrigin Type   = [%s]\n'%(ORIGIN_TYPE_STRINGS[self.origin_type])
        if self.hand_over_type >= 1 and self.hand_over_type <= 3:
            res += '\t\tNetwork ID = [0x%x]\n'%(self.network_id)
        if self.origin_type == 0:
            res += '\t\tInitial service ID = [0x%x]\n'%(self.initial_service_id)
            
    
    def __str__(self):
        res = 'LinkageDescriptor:\n'
        res += '\ttransport stream id = [0x%x]\n'%(self.transport_stream_id)
        res += '\toriginal network id = [0x%x]\n'%(self.original_network_id)
        res += '\tservice id          = [0x%x]\n'%(self.service_id)
        res += '\tlinkage type        = [0x%x]\n'%(self.linkage_type)
        if self.linkage_type == 0x08:
            res += self._get_handover_string()
        return res
    
class CountryAvailabilityDescriptor(Descriptor):
    tag = 0x49
    def __init__(self, data):
        self.available = False
        self.countries = []
        super(CountryAvailabilityDescriptor, self).__init__(data)
    
    def parse(self, data):
        super(CountryAvailabilityDescriptor, self).parse(data)
        flags = data[2]
        if flags & int('10000000',2):
            self.available = True
        loop_len = self.descriptor_length - 1
        offset = 3
        while loop_len >= 3:
            county_data = data[offset:offset+3]
            country = ''.join([chr(x) for x in county_data])
            self.countries.append(country)
            offset += 3
            loop_len -= 3 
        
    def __str__(self):
        res = 'CountryAvailabilityDescriptor:\n'
        temp = 'NOT '
        if self.available: temp = ''
        res += '\tThis service is %savailable in the following countries:\n'%(temp)
        for country in self.countries:
            res += '\tCountry - [%s]\n'%(country)
        return res

class MuxTransportListDescriptor(Descriptor):
    tag = 0x95
    def __init__(self, data):
        self.service_type = None
        self.networks = {}
        self.version = None
        self.behaviour = None
        self.duration = None
        super(MuxTransportListDescriptor, self).__init__(data)
    
    def parse(self, data):
        super(MuxTransportListDescriptor, self).parse(data)
        self.version = data[2]
        self.behaviour = data[3]
        self.duration = (data[4] << 8) + data[5]
        loop_len = self.descriptor_length - 4
        offset = 6
        while loop_len > 0:
            nid = (data[offset] << 8) + data[offset+1]
            self.networks[nid] = []
            tll = data[offset+2]
            offset += 3
            loop_len -= 3
            while tll > 0:
                ts_id = (data[offset] << 8) + data[offset+1]
                self.networks[nid].append(ts_id)
                offset += 2
                tll -= 2
                loop_len -= 3

    def __str__(self):
        res = 'MuxTransportListDescriptor:\n'
        res += '\tVersion   = [%d]\n'%(self.version)
        res += '\tBehaviour = [%s]\n'%(BEHAVIOUR_STRINGS[self.behaviour])
        if self.duration == 0xffff:
            duration = 'infinite'
        else:
            duration = '%d minutes'%(self.duration)
        res += '\tDuration  = [%s]\n'%(duration)
        for nid in self.networks:
            res += '\tNetwork ID [0x%x] has the following TS IDs:\n'%(nid)
            for ts_id in self.networks[nid]:
                res += '\t\tTransport Stream ID [0x%x]\n'%(ts_id)
        return res
    
class MuxSignatureDescriptor(Descriptor):
    tag = 0x96
    def __init__(self, data):
        self.version = None
        self.signature = None
        super(MuxSignatureDescriptor, self).__init__(data)
    
    def parse(self, data):
        super(MuxSignatureDescriptor, self).parse(data)
        self.version = data[2]
        self.signature = data[3:]

    def __str__(self):
        res = 'MuxSignatureDescriptor:\n'
        res += '\tVersion   = [%d]\n'%(self.version)
        res += '\tSignature = [%s]\n'%(str(self.signature))
        return res

class ServiceDescriptor(Descriptor):
    tag = 0x48
    def __init__(self, data):
        self.service_type = None
        self.service_provider_name = ''
        self.service_name = ''
        super(ServiceDescriptor, self).__init__(data)
    
    def parse(self, data):
        super(ServiceDescriptor, self).parse(data)
        self.service_type = data[2]
        service_provider_name_len = data[3]
        pn_offset = 4
        pn_data = data[pn_offset : pn_offset + service_provider_name_len]
        self.service_provider_name = ''.join([chr(x) for x in pn_data])
        
        service_name_len = data[pn_offset + service_provider_name_len]
        sn_offset = pn_offset + service_provider_name_len + 1
        sn_data = data[sn_offset : sn_offset + service_name_len]
        self.service_name = ''.join([chr(x) for x in sn_data])
    
    def __str__(self):
        if self.service_type in SERVICE_TYPE_STRINGS:
            type = SERVICE_TYPE_STRINGS[self.service_type]
        else:
            type = '0x%x'%(self.service_type)
        res = 'ServiceDescriptor:\n'
        res += '\tservice type     = [%s]\n'%(type)
        res += '\tservice name     = [%s]\n'%(self.service_name)
        res += '\tservice provider = [%s]\n'%(self.service_provider_name)
        return res

class ChannelListMappingDescriptor(Descriptor):
    tag = 0x93
    def __init__(self, data):
        self.service_channel_map = {}
        super(ChannelListMappingDescriptor, self).__init__(data)
    
    def parse(self, data):
        super(ChannelListMappingDescriptor, self).parse(data)
        ln = self.descriptor_length
        offset = 2
        while ln > 0:
            service_id     = (data[offset] << 8) + data[offset+1]
            channel_number = (data[offset+2] << 8) + data[offset+3]
            self.service_channel_map[service_id] = channel_number
            ln -= 4
            offset += 4
    
    def __str__(self):
        res = 'ChannelListMappingDescriptor:\n'
        for service_id in self.service_channel_map:
            res += '\tservice id[0x%x] maps to channel number [%d]\n'%(service_id, self.service_channel_map[service_id])
        return res

class BouquetListDescriptor(Descriptor):
    tag = 0x91
    def __init__(self, data):
        self.bouquet_ids = []
        super(BouquetListDescriptor, self).__init__(data)
    
    def parse(self, data):
        super(BouquetListDescriptor, self).parse(data)
        ln = self.descriptor_length
        offset = 2
        while ln > 0:
            bouquet_id = (data[offset] << 8) + data[offset+1]
            self.bouquet_ids.append(bouquet_id)
            ln -= 2
            offset += 2
    
    def __str__(self):
        res = 'BouquetListDescriptor:\n'
        res += '\tThis transport stream has %d bouquets\n'%(len(self.bouquet_ids))
        for i in range(len(self.bouquet_ids)):
            res += '\tBouquet ID [0x%x]\n'%(self.bouquet_ids[i])
        return res
        

class PrivateDataSpecifierDescriptor(Descriptor):
    tag = 0x5F
    def __init__(self, data):
        self.private_data_specifier = 0
        super(PrivateDataSpecifierDescriptor, self).__init__(data)
    
    def parse(self, data):
        super(PrivateDataSpecifierDescriptor, self).parse(data)
        self.private_data_specifier = data[2]
        self.private_data_specifier <<= 8
        self.private_data_specifier += data[3]
        self.private_data_specifier <<= 8
        self.private_data_specifier += data[4]
        self.private_data_specifier <<= 8
        self.private_data_specifier += data[5]

    def __str__(self):
        res = 'PrivateDataSpecifierDescriptor:\n'
        res += '\tprivate data descriptor [' + hex(self.private_data_specifier) + ']\n'
        return res

class OldStylePrivateDataSpecifierDescriptor(PrivateDataSpecifierDescriptor):
    tag = 0x80
    
    def __str__(self):
        res = 'OldStylePrivateDataSpecifierDescriptor:\n'
        res += '\tprivate data descriptor [' + hex(self.private_data_specifier) + ']\n'
        return res

class NetworkNameDescriptor(Descriptor):
    tag = 0x40
    def __init__(self, data):
        self.network_name = ''
        super(NetworkNameDescriptor, self).__init__(data)
    
    def parse(self, data):
        super(NetworkNameDescriptor, self).parse(data)
        nndata = data[2:2+self.descriptor_length]
        self.network_name = ''.join([chr(x) for x in nndata])
            
    def __str__(self):
        res = 'NetworkNameDescriptor:\n'
        res += '\tnetwork name [' + self.network_name + ']\n'
        return res
    
class BouquetNameDescriptor(NetworkNameDescriptor):
    tag = 0x47
    def __init__(self, data):
        self.bouquet_name = ''
        super(BouquetNameDescriptor, self).__init__(data)
    
    def parse(self, data):
        super(BouquetNameDescriptor, self).parse(data)
        self.bouquet_name = self.network_name
            
    def __str__(self):
        res = 'BouquetNameDescriptor:\n'
        res += '\tbouquet name [' + self.bouquet_name + ']\n'
        return res

class ServiceListDescriptor(Descriptor):
    tag = 0x41
    def __init__(self, data):
        self.services = {}
        super(ServiceListDescriptor, self).__init__(data)
    
    def parse(self, data):
        super(ServiceListDescriptor, self).parse(data)
        ln = self.descriptor_length
        offset = 2
        while ln > 0:
            service_id = (data[offset] << 8) + data[offset + 1]
            service_type = data[offset + 2]
            self.services[service_id] = service_type
            ln -= 3
            offset += 3
    
    def __str__(self):
        res = 'ServiceListDescriptor:\n'
        for svc in self.services:
            if self.services[svc] in SERVICE_TYPE_STRINGS:
                type = SERVICE_TYPE_STRINGS[self.services[svc]]
            else:
                type = '0x%x'%(self.services[svc])
            res += '\tservice id [0x%x] -> service type [%s]\n'%(svc, type)
        return res

class SatelliteDeliverySystemDescriptor(Descriptor):
    tag = 0x43
    def __init__(self, data):
        self.desc = {}
        self.east_flag = False
        super(SatelliteDeliverySystemDescriptor, self).__init__(data)
    
    def parse(self, data):
        super(SatelliteDeliverySystemDescriptor, self).parse(data)
        self.frequency = bcd2int(data[2:2+4]) / 100000.0
        self.orbital_pos = bcd2int(data[6:6+2]) / 10.0
        if data[8] & int('10000000', 2):
            self.east_flag = True
        self.polarization = (data[8] & int('01100000', 2)) >> 5
        self.roll_off     = (data[8] & int('00011000', 2)) >> 3
        self.mod_system   = (data[8] & int('00000100', 2)) >> 2
        self.mod_type     =  data[8] & int('00000011', 2)
        self.symbol_rate  = bcd2int(data[9:9+4]) / 10
        self.symbol_rate = self.symbol_rate * 100
        self.fec = data[12] & int('00001111', 2)
        
    def __str__(self):
        res = 'SatelliteDeliverySystemDescriptor:\n'
        res += '\tfrequency      [' + str(self.frequency) + ']\n'
        res += '\torbital pos    [' + str(self.orbital_pos) + ']\n'
        if self.east_flag:
            orbit_part = 'eastern'
        else:
            orbit_part = 'western'
        res += '\torbit part     [' + orbit_part + ']\n'
        res += '\tpolarization   [' + POL_STRINGS[self.polarization] + ']\n'
        res += '\tmodulation sys [' + MOD_SYS_STRINGS[self.mod_system] + ']\n'
        if self.mod_system == MOD_SYS_DVBS2:
            res += '\troll off       [' + str(ROLL_OFF[self.roll_off]) + ']\n'
        res += '\tmodulation type[' + MOD_TYPE_STRINGS[self.mod_type] + ']\n'
        res += '\tsymbol rate    [' + str(self.symbol_rate) + ']\n'
        res += '\tFEC            [' + FEC_STRINGS[self.fec] + ']\n'
        return res
    
    
        
class MultiLingualNetworkNameDescriptor(Descriptor):
    tag = 0x5b
    def __init__(self, data):
        self.names = {}
        super(MultiLingualNetworkNameDescriptor, self).__init__(data)
    
    def parse(self, data):
        super(MultiLingualNetworkNameDescriptor, self).parse(data)
        ln = self.descriptor_length
        offset = 2
        while ln > 0:
            language = ''.join([chr(x) for x in data[offset:offset+3]])
            network_name_length = data[offset + 3]
            nn_data = data[6:6 + network_name_length]
            network_name = ''.join([chr(x) for x in nn_data])
            self.names[language] = network_name
            ln -= (network_name_length + 4)
            offset += (network_name_length + 4)
    
    def __str__(self):
        res = 'MultiLingualNetworkNameDescriptor:\n'
        for language in self.names:
            res += '\tlanguage[' + language + '] -> name[' + self.names[language] + ']\n'
        return res
    
DESC_TABLE = {NetworkNameDescriptor.tag                 :NetworkNameDescriptor,
              SatelliteDeliverySystemDescriptor.tag     :SatelliteDeliverySystemDescriptor,
              MultiLingualNetworkNameDescriptor.tag     :MultiLingualNetworkNameDescriptor,
              ServiceListDescriptor.tag                 :ServiceListDescriptor,
              PrivateDataSpecifierDescriptor.tag        :PrivateDataSpecifierDescriptor,
              OldStylePrivateDataSpecifierDescriptor.tag:OldStylePrivateDataSpecifierDescriptor,
              BouquetListDescriptor.tag                 :BouquetListDescriptor,
              BouquetNameDescriptor.tag                 :BouquetNameDescriptor,
              ChannelListMappingDescriptor.tag          :ChannelListMappingDescriptor,
              ServiceDescriptor.tag                     :ServiceDescriptor,
              MuxTransportListDescriptor.tag            :MuxTransportListDescriptor,
              MuxSignatureDescriptor.tag                :MuxSignatureDescriptor,
              CountryAvailabilityDescriptor.tag         :CountryAvailabilityDescriptor}

for tag in DESC_TABLE:
    descriptors.add_descriptor_class(DESC_TABLE[tag])