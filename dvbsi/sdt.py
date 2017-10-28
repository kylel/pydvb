from mpeg2psi.section import Section
from service import Service
import descriptors

RUNNING_STATUS_UNDEFINED = 0
RUNNING_STATUS_RUNNING = 1
RUNNING_STATUS_STARTS_IN_A_FEW_SECONDS = 2
RUNNING_STATUS_PAUSING = 3
RUNNING_STATUS_RUNNING = 4
RUNNING_STATUS_OFF_AIR = 5

RUNNING_STATUS_STRINGS = {RUNNING_STATUS_UNDEFINED: 'undefined',
                          RUNNING_STATUS_RUNNING  : 'running',
                          RUNNING_STATUS_STARTS_IN_A_FEW_SECONDS: 'starts in a few seconds',
                          RUNNING_STATUS_PAUSING: 'pausing',
                          RUNNING_STATUS_RUNNING: 'running',
                          RUNNING_STATUS_OFF_AIR: 'off air',
                          6: 'reserved',
                          7: 'reserved'}

class ServiceDescription(object):
    """SDT Service description class
    
    An SDT contains a list of service descriptions. Each of these contains service ID, EIT information,
    running status, CA mode, and service descriptors. This class can parse service description data 
    from a SDT and save the relevant information as members.
    """
    def __init__(self):
        """Constructor
        
        This is just a basic constructor. The resulting object will be 'empty'. To gain useful
        information, ServiceDescription.parse() should be called. 
        """
        self.service_id                 = None
        self.eit_schedule_flag          = False
        self.eit_present_following_flag = False
        self.running_status             = None
        self.free_ca_mode               = False
        self.descriptors_length         = None
        self.descriptors                = []
    
    def parse(self, data, offset=0):
        """Parse the given data saving the service information
        
        Parses the given data starting at the given offset to save the service information.
        Once the parsing is complete the offset at which it was completed is returned. This
        allows a loop to process a block of SDT service description data.
        Arguments:
            data   -- array of data bytes to parse to build the elementary stream information
            offset -- the byte offset at which to start the parsing (default 0)
        Returns:
            The byte offset at which this elementary stream data ends
        """
        ln = len(data) - offset
        if ln < 5: #TODO - add exception here
            return None
        self.service_id = (data[0+offset] << 8) + data[1+offset]
        eit_flags = data[2+offset]
        if eit_flags & (int('00000010', 2)):
            self.eit_schedule_flag = True
        if eit_flags & (int('00000001', 2)):
            self.eit_present_following_flag = True      
        ca_rs_flags = data[3+offset]
        self.running_status = ca_rs_flags & (int('11100000', 2))
        self.running_status >>=  5
        if ca_rs_flags & (int('00010000', 2)):
            self.free_ca_mode = True
        self.descriptors_len  = ((data[3+offset] & int('00001111', 2)) << 8) + data[4+offset]
        
        if self.descriptors_len + 5 > ln: #TODO - add exception here
            return None
        
        desc_data = data[5+offset:self.descriptors_len + 5 + offset]
        self.descriptors = descriptors.get_descriptors(desc_data)
        self.length = self.descriptors_len + 5
        return self.descriptors_len + 5 + offset
    
    def get_service_name(self):
        """Returns the name of the service if it exists in the descriptors
        
        Searches the descriptors in the ServiceDescription for Service Descriptor. This descriptor
        will contain the service name. The name will be returned if found.        
        Returns:
            The name of this service. Or None if not found.
        """
        for desc in self.descriptors:
            if type(desc) == descriptors.ServiceDescriptor:
                return desc.service_name
        return None
    
    def get_service_type(self):
        """Returns the type of the service if it exists in the descriptors
        
        Searches the descriptors in the ServiceDescription for Service Descriptor. This descriptor
        will contain the service type which will be returned if found.        
        Returns:
            The type of this service. Or None if not found.
        """
        for desc in self.descriptors:
            if type(desc) == descriptors.ServiceDescriptor:
                return desc.service_type
        return None
                
    
    def __str__(self):
        res = '\tService Loop Item:\n'
        res += '\t\tService ID    [0x%x]\n'%(self.service_id)
        res += '\t\tEIT-S flag    [%s]\n'%(str(self.eit_schedule_flag))
        res += '\t\tEIT-PF flag   [%s]\n'%(str(self.eit_present_following_flag))
        if self.running_status in RUNNING_STATUS_STRINGS:
            res += '\t\tRunning status[%s]\n'%(RUNNING_STATUS_STRINGS[self.running_status])
        else:
            res += '\t\tRunning status[%d]\n'%(self.running_status)
        res += '\t\tFree CA mode  [%s]\n'%(str(self.free_ca_mode))
        res += 'DESCRIPTORS for service 0x%x============================\n' % (self.service_id)
        for desc in self.descriptors:
            res += str(desc)
        res += '==========================================DESCRIPTORS\n'
        return res


class Sdt(Section):
    """Service Description Table class
    
    Inherits from Section and holds information specific to the Service Description Table
    described as a part of DVB SI
    """
    TABLE_ID = 0x42
    PID = 0x11

    def __init__(self, data=None):
        """Constructor
        
        If the given array is None then the SDT object will be created but incomplete. To build the information
        Sdt.parse() or Sdt.add_data() should be called. 
        Arguments:
            data -- array of data bytes to parse to build the section information (default None)
        """
        self.service_loop = []
        super(Sdt, self).__init__(data)

    def parse(self, data=None):
        """Parses the given data to generate all the SDT information
        
        Given an array of bytes that comprise a SDT section, this method will parse and record all the section information
        in object members. Inherits from Section.parse. Will call the Section.parse() method and once complete will parse
        the section table_data to get the SDT specific information.
        Arguments:
            data -- Array of data bytes that describe all or part of the SDT section (default None)
        """
        super(Sdt, self).parse(data)
        if self.complete:
            self.transport_stream_id = self.table_id_extension
            self.payload = self.table_body[5:]
            data = self.payload
            self.original_network_id = (data[0] << 8) + data[1]
            self._get_service_loop_len()
            self._get_service_loop()
            del(self.payload)
            
    def _get_service_loop_len(self):
        """Parses the given data to get the service loop length
        
        Private method used to work out the service loop length in the SDT. The SDT contains a chunk of data that describes
        a loop of service descriptions. This method saves the length, in bytes, of this chunk of data. 
        """
        self.service_loop_length = self.length - 11 - 4
    
    def _get_service_loop_data(self):
        """Returns the service loop data for this SDT
        
        Private method used to return the service loop data chunk from the SDT. The SDT contains a chunk of data that describes
        a loop of service descriptions. This method finds this chunk and returns it as an array of data bytes.
        Returns:
            The service loop data chunk as an array of bytes
        """
        sl_data = self.payload[3:3 + self.service_loop_length]
        return sl_data
    
    def _get_service_loop(self):
        """Generates and saves a list of ServiceDescription objects from the SDT
        
        Private method used to parse the service loop data chunk generating ServiceDescription objects for each service
        in the loop.
        """
        data = self._get_service_loop_data()
        offset = 0
        ln = self.service_loop_length
        self.service_loop = []
        while ln >= 5:
            sd = ServiceDescription()
            offset = sd.parse(data, offset)
            self.service_loop.append(sd)
            ln -= sd.length
    
    def get_double(self):
        """Returns the SDT double (network ID and Transport Stream ID)
        
        Gets the Network ID and Transport Stream ID for this SDT as a tuple.
        Returns:
            A tuple in the format (network ID, transport stream ID)
        """
        return self.original_network_id, self.transport_stream_id
    
    def get_service_name(self, service_id):
        """Returns the service name for the given service ID
        
        Gets the the service name for the given service ID. Searches the SDT descriptors to find one that holds the name
        of the service with the given ID.
        Arguments:
            service_id -- the ID of the service who's name is required
        Returns:
            The name of the service if it is in the SDT. Otherwise None
        """
        for service in self.service_loop:
            if service.service_id == service_id:
                return service.get_service_name()
        return None
    
    def get_service_list(self):
        """Get a list of service objects from the SDT
        
        Builds a list of Service objects from the SDT information. Each service will be populated with as much information
        as possible and saved in a dictionary with the service triplet as a key.
        Returns:
            A dictionary of Service objects keyed by service triplet
        """
        svl = {}
        for service in self.service_loop:
            snam = service.get_service_name()
            stpe = service.get_service_type()
            svc = Service(nid=self.original_network_id, tsid=self.transport_stream_id, svid=service.service_id, name=snam, type=stpe)
            svl[svc.get_triplet()] = svc
        return svl


    def __str__(self):
        res = super(Sdt, self).__str__()
        resar = res.split('\n')
        resar[0] = 'SDT:'
        resar[6] = '\tTransport stream ID [0x%x]\n'%(self.transport_stream_id)
        res = '\n'.join(resar)
        res += ' Service Loop:\n'
        for service in self.service_loop:
            res += str(service)
        return res
    
if __name__ == '__main__':
    print 'Testing Sdt class'
    import unittest
    import _known_tables
    sample_sdt = _known_tables.get_sample_sdt_data()[0]
    
    def testSdtSection(test_case, section):
        test_case.assertEqual(0x42, section.table_id, 'incorrect table id')
        test_case.assertEqual(True, section.section_syntax_indicator, 'incorrect section syntax indicator')
        test_case.assertEqual(True, section.private_indicator, 'incorrect private section indicator')
        test_case.assertEqual(487, section.section_length, 'incorrect section length')
        test_case.assertEqual(16, section.table_id_extension, 'incorrect table id extension')
        test_case.assertEqual(1, section.version, 'incorrect version')
        test_case.assertEqual(0, section.section_number, 'incorrect section number')
        test_case.assertEqual(0, section.last_section_number, 'incorrect last section number')
        test_case.assertEqual(section.section_length, len(section.table_body), 'table body has incorrect length')
        test_case.assertEqual(6144, section.original_network_id, 'table body has incorrect NID')
        test_case.assertEqual('SABC1', section.get_service_name(0x654), 'bad service name')
        test_case.assertEqual(0x2B247EAF, section.crc, 'bad crc')

    class KnownSections(unittest.TestCase):
        known_sections = {testSdtSection:sample_sdt}

        def testKnownSections(self):
            for function in self.known_sections:
                data = self.known_sections[function]
                sdt = Sdt(data)
                function(self, sdt)
                print sdt

    unittest.main()


        