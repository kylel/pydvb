"""Conditional Access Table module

    Provides a CAT Section class to parse and encapsulate information about the
    MPEG2-TS Conditional Access Table section
"""

from section import Section #base class
import descriptors #for descriptors carried in the table

class Cat(Section):
    '''Conditional Access Table class
    
    Inherits from Section and holds information specific to the Conditional Access Table
    described as a part of MPEG2 PSI
    '''
    TABLE_ID = 0x01

    def __init__(self, data=None):
        """Constructor
        
        If the given array is None then the Cat object will be created but incomplete. To build the information
        Cat.parse() or Cat.add_data() should be called. 
        Arguments:
            data -- array of data bytes to parse to build the section information (default None)
        """
        super(Cat, self).__init__(data)

    def parse(self, data):
        """Parses the given data to generate all the Cat information
        
        Given an array of bytes that comprise a CAT section, this method will parse and record all the section information
        in object members. Inherits from Section.parse. Will call the Section.parse() method and once complete will parse
        the section table_data to get the CAT specific information.
        Arguments:
            data -- Array of data bytes that describe all or part of the CAT section (default None)
        """
        super(Cat, self).parse(data)
        if self.complete:
            self.payload = self.table_body[5:]
            desc_data = self.payload[0:-4]
            self.descriptors = descriptors.get_descriptors(desc_data)
            del(self.payload)

    def get_ca_pid(self):
        """Returns the first CA PID found in the CAT descriptors
        
        Searches the descriptors in the CAT for a Conditional Access Descriptor. As soon as one is found its CA PID value
        is returned. When the CA descriptor is found in a CAT, the CA PID points to packets containing system-wide and/or
        access control management information, such as EMMs.
        Returns:
            The first CA PID found in the CAT descriptors. Returns None if a CA PID is not found.
        """
        for desc in self.descriptors:
            if type(desc) == descriptors.ConditionalAccessDescriptor:
                return desc.ca_pid
        return None
    
    def get_ca_pids(self):
        """Returns the all the CA PIDs found in the CAT descriptors
        
        Searches the descriptors in the CAT for Conditional Access Descriptors. Each descriptor's CA PID value is saved
        in a dictionary with the CA system ID as the key. When the CA descriptor is found in a CAT, the CA PID points to
        packets containing system-wide and/or access control management information, such as EMMs.
        Returns:
            The a dictionary of CA PIDs with their corresponding CA system IDs as keys. If none are found then an empty
            dictionary is returned.
        """
        pids = {}
        for desc in self.descriptors:
            if type(desc) == descriptors.ConditionalAccessDescriptor:
                pids[desc.ca_system_id] = desc.ca_pid
        return pids

    def __str__(self):
        res = super(Cat, self).__str__()
        resar = res.split('\n')
        resar[0] = 'CAT:'
        resar[6] = ''
        res = '\n'.join(resar)
        for desc in self.descriptors:
            res += str(desc)
        
        return res


'''UNIT TESTS -------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------------
'''
if __name__ == '__main__':
    print 'Testing Cat class'
    #TODO - not a full unit test - need to do partial data addition
    import unittest
    import _known_tables
    
    cat_section = _known_tables.get_sample_cat_data()[0]
     
    def testCatSection(test_case, section):
        test_case.assertEqual(1, section.table_id, 'incorrect table id')
        test_case.assertEqual(True, section.section_syntax_indicator, 'incorrect section syntax indicator')
        test_case.assertEqual(False, section.private_indicator, 'incorrect private section indicator')
        test_case.assertEqual(15, section.section_length, 'incorrect section length')
        #test_case.assertEqual(0, section.table_id_extension, 'incorrect table id extension') Not used for a CAT
        test_case.assertEqual(0, section.version, 'incorrect version')
        test_case.assertEqual(0, section.section_number, 'incorrect section number')
        test_case.assertEqual(0, section.last_section_number, 'incorrect last section number')
        test_case.assertEqual(section.section_length, len(section.table_body), 'table body has incorrect length')
        test_case.assertEqual(1280, section.get_ca_pid())
        test_case.assertEqual({1542:1280}, section.get_ca_pids())
        test_case.assertEqual(0x9064c6d0, section.crc, 'bad crc')
        
    class KnownSections(unittest.TestCase):
        known_sections = {testCatSection:cat_section}
        
        def testKnownSections(self):
            for function in self.known_sections:
                data = self.known_sections[function]
                cat = Cat(data)
                function(self, cat)                            
                
    unittest.main()