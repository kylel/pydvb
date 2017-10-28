"""Basic Network Information Table and Bouquet Information Table module

    Provides a BAT/NIT base section class to parse and encapsulate information about the
    DVBSI, Network Information Table or Bouquet Information Table section. These two can be grouped
    together into one base class since they share an identical structure.
"""

from mpeg2psi.section import Section
from service import Service
import descriptors
       
class TsItem(object):
    """Transport Stream Item class
    
    Each BAT/NIT contains a list of Transport Stream descriptions. Each one holds the TS ID, the
    original network ID and a set of descriptors specific to the TS. This class can parse TS loop
    data in a BAT or NIT and save the relevant information as members.
    """
    def __init__(self):
        """Constructor
        
        This is just a basic constructor. The resulting object will be 'empty'. To gain useful
        information, TsItem.parse() should be called. 
        """
        self.transport_stream_id = None
        self.original_network_id = None
        self.ts_descriptors_len  = None
        self.descriptors = []
    
    def get_satellite_delivery_descriptor(self):
        """Gets the satellite delivery descriptor if it exists
        
        Searches the descriptors in the TSItem for a satellite delivery descriptor. Once one is
        found, it is returned.        
        Returns:
            A SatelliteDeliverySystemDescriptor object or None
        """
        #print 'looking for satellite_delivery_descriptor'
        for desc in self.descriptors:
            #print 'checking desc [%s]'%(str(type(desc)))
            if type(desc) == descriptors.SatelliteDeliverySystemDescriptor:
                #print 'GOT the descriptor and returning it!!!!'
                return desc
        #print 'DID NOT GOT the descriptor and returning it!!!!'
        return None
    
    def get_channel_number(self, service_id):
        """Gets the channel number for the given service ID
        
        Searches through the TsItem descriptors for a ChannelListMappingDescriptor. If one is found
        then it will be used to map the service ID to a channel number which will be returned.
        Arguments:
            service_id -- id of the service who's channel number should be found. Should belong to
            the TS described by this object
        Returns:
            The channel number of the given service or None
        """
        for desc in self.descriptors:
            if type(desc) == descriptors.ChannelListMappingDescriptor:
                if service_id in desc.service_channel_map:
                    return desc.service_channel_map[service_id]
        return None
    
    def get_service_list(self):
        """Gets a list of Service objects in this TsItem
        
        Searches through the TsItem descriptors for descriptors of type ServiceListDescriptor
        and ChannelListMappingDescriptor. The information from both of these descriptors is used
        to build a dictionary objects keyed by service triplet.
        Returns:
            A dictionary of Service objects keyed by service triplet or None
        """
        svl_types    = {}
        svl_channels = {}
        svl = {}
        for desc in self.descriptors:
            if type(desc) == descriptors.ServiceListDescriptor:
                svl_types = desc.services
            if type(desc) == descriptors.ChannelListMappingDescriptor:
                svl_channels = desc.service_channel_map
        
        if len(svl_types) > 0: svl_iterator = svl_types
        elif len(svl_channels) > 0: svl_iterator = svl_channels
        else: return None#TODO - should select the longest list to iterate with
        
        for service_id in svl_iterator:
            ts_id = self.transport_stream_id
            n_id = self.original_network_id
            channel = None
            stpe = None
            if service_id in svl_channels:
                channel = svl_channels[service_id]
            if service_id in svl_types:
                stpe = svl_types[service_id]
            svc  = Service(nid=n_id, tsid=ts_id, svid=service_id, chan=channel, type=stpe)
            svl[(n_id, ts_id, service_id)] = svc
        return svl

    def get_double(self):
        """Returns the TsItem double (network ID and Transport Stream ID)
        
        Gets the Network ID and Transport Stream ID for this TS as a tuple.
        Returns:
            A tuple in the format (network ID, transport stream ID)
        """
        return self.original_network_id, self.transport_stream_id
    
    def parse(self, data, offset=0):
        """Parse the given data saving the Transport Stream information
        
        Parses the given data starting at the given offset to save the TS information.
        Once the parsing is complete the offset at which it was completed is returned. This
        allows a loop to process a block of NIT/BAT TS loop data.
        Arguments:
            data   -- array of data bytes to parse to build the transport stream information
            offset -- the byte offset at which to start the parsing (default 0)
        Returns:
            The byte offset at which this transport stream data ends
        """
        ln = len(data) - offset
        if ln < 6:#TODO - exception here
            return None
        self.transport_stream_id = (data[0+offset] << 8) + data[1+offset]
        self.original_network_id = (data[2+offset] << 8) + data[3+offset]
        self.ts_descriptors_len  = ((data[4+offset] & int('00001111', 2)) << 8) + data[5+offset]
        if self.ts_descriptors_len + 6 > ln:#TODO - exception here
            return None
        desc_data = data[6+offset:self.ts_descriptors_len + 6 + offset]
        self.descriptors = descriptors.get_descriptors(desc_data)
        self.length = self.ts_descriptors_len + 6
        return self.ts_descriptors_len + 6 + offset
    
    def __str__(self):
        res = '\tTransport Stream Loop Item:\n'
        res += '\t\ttransport stream ID[%d]\n'%(self.transport_stream_id)
        res += '\t\toriginal network ID[%d]\n'%(self.original_network_id)
        res += 'DESCRIPTORS for ts %s============================\n' % (str(str(self.transport_stream_id)))
        for desc in self.descriptors:
            res += str(desc)
        res += '==========================================DESCRIPTORS\n'
        return res

class BatNitBase(Section):
    """Base class for both BAT and NIT classes
    
    Inherits from Section. The BAT and NIT in DVB SI have an almost identical format. This
    class encompasses all these similarities in a generic base class to avoid repetition.
    """
    def __init__(self, data=None):
        """Constructor
        
        If the given array is None then the BAT/NIT object will be created but incomplete. To build the information
        BatNitBase.parse() or BatNitBase.add_data() should be called. 
        Arguments:
            data -- array of data bytes to parse to build the section information (default None)
        """
        self.descriptors   = []
        self.ts_loop       = []
        super(BatNitBase, self).__init__(data)
    
    def parse(self, data=None):
        """Parses the given data to generate all the BAT/NIT information
        
        Given an array of bytes that comprise a BAT/NIT section, this method will parse and record all the section information
        in object members. Inherits from Section.parse. Will call the Section.parse() method and once complete will parse
        the section table_data to get the BAT/NIT specific information.
        Arguments:
            data -- Array of data bytes that describe all or part of the BAT/NIT section (default None)
        """
        super(BatNitBase, self).parse(data)
        if self.complete:
            self.payload = self.table_body[5:]
            self._get_descriptors_len()
            desc_data        = self.payload[2:2+self.descriptors_len]
            self.descriptors = descriptors.get_descriptors(desc_data)
            self._get_ts_loop_len()
            self._get_ts_loop()
            del(self.payload)
            
    def _get_descriptors_len(self):
        """Saves the length of the block of data holding the BAT/NIT descriptors
        
        Private method that parses the section data to find and save the length of the block of data that holds the descriptors that are specific
        to this BAT/NIT.  
        """
        data = self.payload
        self.descriptors_len = ((data[0] & int('00001111', 2)) << 8) + data[1]
    
    def _get_ts_loop_len(self):
        """Saves the length of the block of data holding the transport stream loop
        
        Private method that parses the section data to find and save the length of the block of data that holds the transport stream loop.  
        """
        dl = self.descriptors_len
        data = self.payload
        offset = 2 + dl
        tsll = ((data[offset] & int('00001111', 2)) << 8) + data[offset + 1]  
        self.ts_loop_len = tsll
    
    def _get_ts_loop_data(self):
        """Saves the the block of data holding the transport stream loop
        
        Private method that parses the section data to find and save the block of data that holds the transport stream loop in a local
        member. It is saved as a list of bytes.  
        """
        offset = 4 + self.descriptors_len
        tsl_data = self.payload[offset:offset + self.ts_loop_len]
        return tsl_data
    
    def _get_ts_loop(self):
        """Generates a list of TsItem objects to describe the BAT/NIT TS loop
        
        Private method that parses the block of data containing the transport stream loop and generates a list of TsItem objects to
        describe each TS in the loop.  
        """
        data = self._get_ts_loop_data()
        offset = 0
        ln = self.ts_loop_len
        self.ts_loop = []
        while ln >= 6:
            tsi = TsItem()
            offset = tsi.parse(data, offset)
            self.ts_loop.append(tsi)
            ln -= tsi.length
    
    def get_channel_number(self, service_id, ts_id=None):
        """Gets the channel number for the given service ID
        
        Gets the the channel number for the given service ID. Searches the TsItems in the
        transport stream loop for the transport stream with the given ID. Then the TsItem
        object for that TS is queried to get the channel number for the given service ID.
        Arguments:
            service_id -- ID of the service who's channel is required
            ts_id      -- ID of the transport stream that contains the service (default None)
                          If this is None, then every TS will be checked for the given
                          service ID
        Returns:
            The channel of the service if it is in the NIT/BAT. Otherwise None
        """
        if ts_id == None:
            for ts in self.ts_loop:
                chan = ts.get_channel_number(service_id)
                if chan != None: return chan
        else:
            for ts in self.ts_loop:
                if ts.transport_stream_id == ts_id:
                    chan = ts.get_channel_number(service_id)
                    if chan != None: return chan
        return None
    
    def get_doubles(self):
        """Gets a list of doubles (network ID, transport stream ID) for each TS in this table
        
        Generates a list of doubles (network ID, TS ID) for each transport stream described in
        this table.
        Returns:
            List of doubles in tuple format
        """
        doubles = []
        for ts in self.ts_loop:
            doubles.append(ts.get_double())
        return doubles
    
    def get_network_id(self):
        net_ids = []
        doubles = self.get_doubles()
        for double in doubles:
            net_ids.append(double[0])
        net_ids = list(set(net_ids))
        return net_ids
    
    def get_ts_list(self):
        """Gets a list of transport stream IDs described in this table
        
        Generates a list transport stream IDs described in this table.
        Returns:
            List of transport stream IDs
        """
        ts_list = []
        for ts in self.ts_loop:
            ts_list.append(ts.transport_stream_id)
        return ts_list
    
    def get_service_list(self, ts_id):
        """Gets a list of Service objects for the given transport stream
        
        Finds the transport stream information for the given TS ID by searching the TS loop.
        Then queries the TsItem to get a list of Service objects.
        Returns:
            A dictionary of Service objects keyed by service triplet or None
        """
        for ts in self.ts_loop:
            if ts.transport_stream_id == ts_id:
                return ts.get_service_list()

    def get_all_service_lists(self):
        """Gets a list of Service objects described in this table
        
        Searches the entire table for all services and returns a dictionary of service
        lists for each transport stream described in the table.
        Returns:
            A dictionary of Service Lists keyed by (network ID, transport stream ID)
        """
        service_lists = {}
        for ts in self.ts_loop:
            service_lists[ts.original_network_id, ts.transport_stream_id] = ts.get_service_list()
        return service_lists
            
    def __str__(self):
        res = super(BatNitBase, self).__str__()
        resar = res.split('\n')
        resar[0] = 'BAT/NIT:'
        resar[6] = '\tID       [%d]\n'%(self.table_id_extension)
        res = '\n'.join(resar)
        if len(self.descriptors) > 0:
            res += ' Descriptors:\n'
            for net_des in self.descriptors:
                res += str(net_des) 
        res += ' Transport Stream Loop:\n'
        for ts in self.ts_loop:
            res += str(ts)
        return res

'''UNIT TESTS -------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------------
'''
if __name__ == '__main__':
    print 'Testing BatNitBase class'
    import unittest
    import _known_tables
    
    sample_bat = _known_tables.get_sample_bat_data()[0]
    sample_nit_0 = _known_tables.get_sample_nit_data()[0]
    sample_nit_1 = _known_tables.get_sample_nit_data()[1]
        
    def testNitSection0(test_case, section):
        test_case.assertEqual(64, section.table_id, 'incorrect table id')
        test_case.assertEqual(True, section.section_syntax_indicator, 'incorrect section syntax indicator')
        test_case.assertEqual(True, section.private_indicator, 'incorrect private section indicator')
        test_case.assertEqual(0x3f6, section.section_length, 'incorrect section length')
        test_case.assertEqual(6144, section.table_id_extension, 'incorrect table id extension')
        test_case.assertEqual(1, section.version, 'incorrect version')
        test_case.assertEqual(0, section.section_number, 'incorrect section number')
        test_case.assertEqual(1, section.last_section_number, 'incorrect last section number')
        test_case.assertEqual(section.section_length, len(section.table_body), 'table body has incorrect length')
        test_case.assertEqual([20, 2, 3, 4, 5, 16, 136, 19, 21, 10], section.get_ts_list(), 'incorrect ts list')
        doubles = [(6144, 20), (6144, 2), (6144, 3), (6144, 4), (6144, 5), (6144, 16), (6144, 136), (6144, 19), (6144, 21), (6144, 10)]
        test_case.assertEqual(doubles, section.get_doubles(), 'incorrect doubles')
        test_case.assertEqual(None, section.get_channel_number(0x235, 5), 'incorrect channel number')
        test_case.assertEqual(None, section.get_channel_number(0x235), 'incorrect channel number')
        test_case.assertEqual(0xD9787E8A, section.crc, 'bad crc')
    
    def testNitSection1(test_case, section):
        test_case.assertEqual(64, section.table_id, 'incorrect table id')
        test_case.assertEqual(True, section.section_syntax_indicator, 'incorrect section syntax indicator')
        test_case.assertEqual(True, section.private_indicator, 'incorrect private section indicator')
        test_case.assertEqual(0x91, section.section_length, 'incorrect section length')
        test_case.assertEqual(6144, section.table_id_extension, 'incorrect table id extension')
        test_case.assertEqual(1, section.version, 'incorrect version')
        test_case.assertEqual(1, section.section_number, 'incorrect section number')
        test_case.assertEqual(1, section.last_section_number, 'incorrect last section number')
        test_case.assertEqual(section.section_length, len(section.table_body), 'table body has incorrect length')
        test_case.assertEqual([11, 12, 13], section.get_ts_list(), 'incorrect ts list')
        doubles = [(6144, 11), (6144, 12), (6144, 13)]
        test_case.assertEqual(doubles, section.get_doubles(), 'incorrect doubles')
        test_case.assertEqual(None, section.get_channel_number(0x235, 5), 'incorrect channel number')
        test_case.assertEqual(None, section.get_channel_number(0x235), 'incorrect channel number')
        test_case.assertEqual(0xCF1BECB1, section.crc, 'bad crc')
    
    def testBatSection(test_case, section):
        test_case.assertEqual(74, section.table_id, 'incorrect table id')
        test_case.assertEqual(True, section.section_syntax_indicator, 'incorrect section syntax indicator')
        test_case.assertEqual(True, section.private_indicator, 'incorrect private section indicator')
        test_case.assertEqual(0x1d3, section.section_length, 'incorrect section length')
        test_case.assertEqual(10, section.table_id_extension, 'incorrect table id extension')
        test_case.assertEqual(2, section.version, 'incorrect version')
        test_case.assertEqual(0, section.section_number, 'incorrect section number')
        test_case.assertEqual(0, section.last_section_number, 'incorrect last section number')
        test_case.assertEqual(section.section_length, len(section.table_body), 'table body has incorrect length')
        test_case.assertEqual([2, 5, 16, 20, 21, 136], section.get_ts_list(), 'incorrect ts list')
        doubles = [(6144, 2), (6144, 5), (6144, 16), (6144, 20), (6144, 21), (6144, 136)]
        test_case.assertEqual(doubles, section.get_doubles(), 'incorrect doubles')
        test_case.assertEqual(300, section.get_channel_number(0x235, 5), 'incorrect channel number')
        test_case.assertEqual(300, section.get_channel_number(0x235), 'incorrect channel number')
        test_case.assertEqual(0x848D251C, section.crc, 'bad crc')

    class KnownSections(unittest.TestCase):
        known_sections = {testBatSection:sample_bat,
                          testNitSection0:sample_nit_0,
                          testNitSection1:sample_nit_1}

        def testKnownSections(self):
            for function in self.known_sections:
                data = self.known_sections[function]
                batnit = BatNitBase(data)
                #print batnit.get_doubles()
                #print batnit.get_ts_list()
                #print batnit
                #print batnit.get_channel_number(0x235, 5)
                #print batnit.get_channel_number(0x235, None)
                print batnit.get_service_list(5)
                function(self, batnit)

    unittest.main()


        
    