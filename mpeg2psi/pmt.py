"""Program Map Table module

    Provides a set of functions and a PMT Section class to parse and encapsulate information about a
    MPEG2-TS Program Map Table section
"""

from section import Section
import descriptors

def get_pcr_pid(data):
    """Get the PCR PID from the given section data
    
    Parses the given array of PMT section data bytes to find the PCR PID.
    Arguments:
        data -- An array of data bytes representing the PMT payload
    Returns:
         The PCR PID value for this PMT
    """
    pcr_pid = int('00011111', 2) & data[0]
    pcr_pid = pcr_pid << 8
    pcr_pid = pcr_pid + data[1]
    return pcr_pid

def get_program_info_length(data):
    """Get the program information length from the given section data
    
    Parses the given array of PMT section data bytes to find the program information length. This
    is the length of the data containing descriptors that describe this program.
    Arguments:
        data -- An array of data bytes representing the PMT payload
    Returns:
         The program information length in bytes
    """
    pi_len = int('00001111', 2) & data[2]
    pi_len = pi_len << 8
    pi_len = pi_len + data[3]
    return pi_len

def get_program_info_data(data):
    """Get the program information data from the given section data
    
    Parses the given array of PMT section data bytes to find the program information data. This
    is the data containing descriptors that describe this program.
    Arguments:
        data -- An array of data bytes representing the PMT payload
    Returns:
         The program information data as an array of bytes
    """
    len = get_program_info_length(data)
    pi_data = data[4:4+len]
    return pi_data

def get_elementary_stream_offset(data):
    """Get the elementary stream offset from the given section data
    
    Parses the given array of PMT section data bytes to find the byte offset where the elementary
    stream information begins.
    Arguments:
        data -- An array of data bytes representing the PMT payload
    Returns:
         The number of bytes from the beginning of the section payload to the beginning of the
         elementary stream data.
    """
    pil =  get_program_info_length(data)
    offset = 4 + pil
    return offset

class PmtElementaryStream(object):
    """PMT elementary stream class
    
    Each PMT contains a list of elementary streams. Each one holds the stream type, PID and
    a set of descriptors for the stream. This class can parse elementary stream data from a PMT
    and save the relevant information as members.
    """
    def __init__(self):
        """Constructor
        
        This is just a basic constructor. The resulting object will be 'empty'. To gain useful
        information, PmtElementaryStream.parse() should be called. 
        """
        self.stream_type = None
        self.pid = None
        self.es_info_length = None
        self.es_data = None
        self.descriptors = []
        
    def parse(self, data, offset):
        """Parse the given data saving the elementary stream information
        
        Parses the given data starting at the given offset to save the elementary stream
        information. Once the parsing is complete the offset at which it was completed is
        returned. This allows a loop to process a block of PMT elementary stream data.
        Arguments:
            data   -- array of data bytes to parse to build the elementary stream information
            offset -- the byte offset at which to start the parsing
        Returns:
            The byte offset at which this elementary stream data ends
        """
        self.stream_type = data[offset]
        self.pid = data[offset+1] & int('00011111', 2)
        self.pid = self.pid << 8
        self.pid = self.pid + data[offset + 2]
        self.es_info_length = data[offset+3] & int('00001111', 2)
        self.es_info_length = self.es_info_length << 8
        self.es_info_length = self.es_info_length + data[offset+4]
        self.es_data = data[offset+5:offset+5+self.es_info_length]
        self.descriptors = descriptors.get_descriptors(self.es_data)
        return 5 + self.es_info_length
    
    def get_ca_pids(self):
        """Returns the all the CA PIDs found in the elementary stream (ES) descriptors
        
        Searches the descriptors in the ES for Conditional Access Descriptors. Each descriptor's CA PID value is saved
        in a list. When the CA descriptor is found in a PMT ES, the CA PID points to packets containing program 
        related access control information, such as ECMs. In this case the PIDs apply to the specific program element.        
        Returns:
            A list of CA PIDs. If none are found then an empty list is returned.
        """
        pids = []
        for desc in self.descriptors:
            if type(desc) == descriptors.ConditionalAccessDescriptor:
                pids.append(desc.ca_pid)
        return pids
    
    def __str__(self):
        if self.stream_type == None: return '\tempty'
        res = '\tElementary Stream Loop:\n'
        res += '\t\tStream Type[%d]\n'%(self.stream_type)
        res += '\t\tPID[0x%x]\n'%(self.pid)
        res += '\t\tES info length[%d]\n'%(self.es_info_length)
        for desc in self.descriptors:
            res += str(desc)
        return res

def get_elementary_stream_loop(data):
    """Gets a list of PmtElementaryStream objects from PMT payload
    
    Given an array of data bytes in the PMT payload, a list of  PmtElementaryStream objects will
    be instantiated to represent this data.
    Arguments:
        data -- An array of data bytes representing the PMT payload
    Returns:
        A list of PmtElementaryStream objects representing the fully parsed ES loop
    """
    es_loop = []
    offset = get_elementary_stream_offset(data)
    length = len(data) - 4 - offset
    while length >= 5:
        esd = PmtElementaryStream()
        esd_len = esd.parse(data, offset)
        length -= esd_len
        offset += esd_len
        es_loop.append(esd)
    return es_loop  
    
class Pmt(Section):
    """Program Map Table class
    
    Inherits from Section and holds information specific to the Program Map Table
    described as a part of MPEG2 PSI
    """
    TABLE_ID = 0x02

    def __init__(self, data=None):
        """Constructor
        
        If the given array is None then the PMT object will be created but incomplete. To build the information
        Pmt.parse() or Pmt.add_data() should be called. 
        Arguments:
            data -- array of data bytes to parse to build the section information (default None)
        """
        self.descriptors = []
        super(Pmt, self).__init__(data)


    def parse(self, data):
        """Parses the given data to generate all the PMT information
        
        Given an array of bytes that comprise a PMT section, this method will parse and record all the section information
        in object members. Inherits from Section.parse. Will call the Section.parse() method and once complete will parse
        the section table_data to get the PMT specific information.
        Arguments:
            data -- Array of data bytes that describe all or part of the PAT section (default None)
        """
        super(Pmt, self).parse(data)
        self.program_number = self.table_id_extension
        if self.complete:
            self.payload = self.table_body[5:]
            self.pcr_pid = get_pcr_pid(self.payload)
            self.program_info_length = get_program_info_length(self.payload)
            self.program_info_data = get_program_info_data(self.payload)
            self.descriptors = descriptors.get_descriptors(self.program_info_data)
            self._get_es_loop(self.payload)
            del(self.payload)
    
    def get_pids(self):
        """Returns all the PIDs belonging to this program
        
        Builds a list of all the PIDs in the program.
        Returns:
            A list of every PID in the program including the PCR PID. Does not include CA PIDs found in the descriptors. 
        """
        pids = []
        if self.pcr_pid != 0x1fff:
            pids.append(self.pcr_pid)
        for es in self.es_loop:
            pids.append(es.pid)
        pids = list(set(pids))# remove duplicates
        return pids 
    
    def get_ca_pid(self):
        """Returns the first CA PID found in the PMT descriptors
        
        Searches the descriptors in the PMT for a Conditional Access Descriptor. As soon as one is found its CA PID value
        is returned. When the CA descriptor is found in a PMT, the CA PID points to packets containing program related 
        access control information, such as ECMs.
        Returns:
            The first CA PID found in the PMT descriptors. Returns None if a CA PID is not found.
        """
        for desc in self.descriptors:
            if type(desc) == descriptors.ConditionalAccessDescriptor:
                return desc.ca_pid
        return None
    
    def get_ca_pids(self):
        """Returns the all the CA PIDs found in the PMT descriptors
        
        Searches the descriptors in the PMT for Conditional Access Descriptors. Each descriptor's CA PID value is saved
        in list. When the CA descriptor is found in a PMT, the CA PID points to packets containing program related 
        access control information, such as ECMs. All the descriptors in the PMT are parsed including the elementary
        stream descriptors.
        Returns:
            The a list CA PIDs. If none are found then an empty list is returned.
        """
        pids = []
        for desc in self.descriptors:
            if type(desc) == descriptors.ConditionalAccessDescriptor:
                pids.append(desc.ca_pid)
        for es in self.es_loop:
            pids.extend(es.get_ca_pids())
        return pids
    
    def get_all_pids(self):
        """Returns all the PIDs belonging to this program including CA specific ones
        
        Builds a list of all the PIDs in the program including CA pids.
        Returns:
            A list of every PID in the program including the PCR PID and CA PIDs. 
        """
        pids = []
        pids.extend(self.get_pids()) 
        pids.extend(self.get_ca_pids())
        pids = list(set(pids))
        return pids
    
    def _get_es_loop(self, data):
        """Parses the given data to get the elementary stream information
        
        Private method used to generate a list of PmtElementaryStream objects from elementary stream loop
        data in the PMT 
        Arguments:
            data -- array section data bytes in the PMT payload
        """
        self.es_loop = get_elementary_stream_loop(data)
        
    def __str__(self):
        res = super(Pmt, self).__str__()
        resar = res.split('\n')
        resar[0] = 'PMT:'
        resar[6] = '\n\tProgram Number[%d]\n'%(self.program_number)
        res = '\n'.join(resar)
        res += '\tPCR PID[%d]\n'%(self.pcr_pid)
        res += '\tprogram info length[%d]\n'%(self.program_info_length)
        for desc in self.descriptors:
            res += str(desc)
        for es in self.es_loop:
            res += str(es)
        return res

'''UNIT TESTS -------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------------
'''
if __name__ == '__main__':
    print 'Testing Pmt class'
    import unittest
    import _known_tables
    sample_pmt = _known_tables.get_sample_pmt_data()[0]
    
    def testPmtSection(test_case, section):
        test_case.assertEqual(2, section.table_id, 'incorrect table id')
        test_case.assertEqual(True, section.section_syntax_indicator, 'incorrect section syntax indicator')
        test_case.assertEqual(False, section.private_indicator, 'incorrect private section indicator')
        test_case.assertEqual(72, section.section_length, 'incorrect section length')
        test_case.assertEqual(0x3f2, section.table_id_extension, 'incorrect table id extension')
        test_case.assertEqual(0x3f2, section.program_number, 'incorrect program number')
        test_case.assertEqual(1, section.version, 'incorrect version')
        test_case.assertEqual(0, section.section_number, 'incorrect section number')
        test_case.assertEqual(0, section.last_section_number, 'incorrect last section number')
        test_case.assertEqual(section.section_length, len(section.table_body), 'table body has incorrect length')
        test_case.assertEqual(1524, section.get_ca_pid(), 'incorrect ca pid')
        test_case.assertEqual([1524], section.get_ca_pids(), 'incorrect ca pids')
        test_case.assertEqual([2003, 2004, 2005, 2006], section.get_pids(), 'incorrect pids')
        test_case.assertEqual([1524, 2003, 2004, 2005, 2006], section.get_all_pids(), 'incorrect pids')
        test_case.assertEqual(0x11f62c03, section.crc, 'bad crc')

    class KnownSections(unittest.TestCase):
        known_sections = {testPmtSection:sample_pmt}

        def testKnownSections(self):
            for function in self.known_sections:
                data = self.known_sections[function]
                pmt = Pmt(data)
                #print pmt.get_all_pids()
                #print pmt
                #print pmt.get_pids()
                function(self, pmt)
                print pmt

    unittest.main()