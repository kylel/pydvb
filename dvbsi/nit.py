"""Network Information Table module

    Provides a NIT section class to parse and encapsulate information about the DVBSI
    Network Information Table.
"""

from bat_nit_base import BatNitBase

class Nit(BatNitBase):
    """Network Information Table class
    
    Inherits from BatNitBase and holds information specific to the Network Information Table
    described as a part of DVB SI
    """
    TABLE_ID = 0x40
    
    def parse(self, data=None):
        """Parses the given data to generate all the NIT information
        
        Given an array of bytes that comprise a NIT section, this method will parse and record all the section information
        in object members. Inherits from BatNitBase.parse. Will call the BatNitBase.parse() method and once complete will parse
        the section table_data to get the NIT specific information.
        Arguments:
            data -- Array of data bytes that describe all or part of the NIT section (default None)
        """
        super(Nit, self).parse(data)
        if self.complete:
            self.network_id = self.table_id_extension

    def get_satellite_delivery_descriptor(self, tsid):
        """Get satellite delivery descriptor for the given TS
        
        Parses all the NIT descriptors until a satellite delivery descriptor is found. If it is found it is returned.
        Arguments:
            tsid -- Transport stream ID of the TS who's satellite parameters are required
        Returns:
            A descriptor of type SatelliteDeliverySystemDescriptor or None
        """
        #print 'gettting SDD for this NIT -- tsid = %d'%(tsid)
        for ts in self.ts_loop:
            #print 'gettting SDD for this NIT -- checking ts: [%s]'%(str(ts))
            if ts.transport_stream_id == tsid:
                #print 'it is correct'
                return ts.get_satellite_delivery_descriptor()
        return None

    def __str__(self):
        res = super(Nit, self).__str__()
        resar = res.split('\n')
        resar[0] = 'NIT:'
        resar[6] = '\tNetwork ID       [%d]\n'%(self.table_id_extension)
        res = '\n'.join(resar)
        return res
    
'''UNIT TESTS -------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------------
'''
if __name__ == '__main__':
    print 'Testing Nit class'
    import unittest
    import _known_tables
    
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
    
    class KnownSections(unittest.TestCase):
        known_sections = {testNitSection0:sample_nit_0,
                          testNitSection1:sample_nit_1}

        def testKnownSections(self):
            import service_list
            for function in self.known_sections:
                data = self.known_sections[function]
                nit = Nit(data)
                function(self, nit)
                svl = service_list.ServiceList()
                svl.update(nit=nit)
                print nit
                print svl
            print svl
            
    unittest.main()


        
    