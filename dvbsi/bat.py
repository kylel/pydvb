"""Bouquet Information Table module

    Provides a BAT section class to parse and encapsulate information about the DVBSI
    Bouquet Information Table.
"""

from bat_nit_base import BatNitBase
import descriptors

class Bat(BatNitBase):
    """Bouquet Information Table class
    
    Inherits from BatNitBase and holds information specific to the Bouquet Information Table
    described as a part of DVB SI
    """
    TABLE_ID = 0x4A
    
    def parse(self, data=None):
        """Parses the given data to generate all the BAT information
        
        Given an array of bytes that comprise a BAT section, this method will parse and record all the section information
        in object members. Inherits from BatNitBase.parse. Will call the BatNitBase.parse() method and once complete will parse
        the section table_data to get the BAT specific information.
        Arguments:
            data -- Array of data bytes that describe all or part of the BAT section (default None)
        """
        super(Bat, self).parse(data)
        if self.complete:
            self.bouquet_id = self.table_id_extension
    
    def get_name(self):
        """Get name of this Bouquet
        
        Parses all the BAT descriptors until a BouquetNameDescriptor is found. If not found, None is returned. If it is, then the
        name of the bouquet described by this table will be returned.
        Returns:
            The name of the bouquet or None
        """
        for desc in self.descriptors:
            if type(desc) == descriptors.BouquetNameDescriptor:
                return  desc.bouquet_name
        return None

    def get_bouquet_list(self):
        """Get a list of Bouquet IDs if this table has one
        
        Parses all the BAT descriptors until a BouquetListDescriptor is found. If not found None is returned. If it is, then the
        list of bouquet IDs in this descriptor is returned
        Returns:
            The name of the bouquet or None
        """
        for desc in self.descriptors:
            if type(desc) == descriptors.BouquetListDescriptor:
                return desc.bouquet_ids
        return None
    
    def get_eits_service_info(self):
        """Get the service ID and the transport stream ID of the EITS service
        
        Parses all the BAT descriptors until a IrdetoLinkageDescriptor is found. This descriptor provides information on where
        the EITS service is located. If one is found, the EITS service TS ID and service ID are returned.
        Returns:
            The EITS service ID and transport stream ID in tuple format (ts_id, service_id)
        """
        for desc in self.descriptors:
            if type(desc) == descriptors.IrdetoLinkageDescriptor:
                if desc.eits_transport_stream_id != None:
                    return (desc.eits_transport_stream_id, desc.eits_service_id)
        return None
    
    def __str__(self):
        res = super(Bat, self).__str__()
        resar = res.split('\n')
        resar[0] = 'BAT:'
        resar[6] = '\tBouquet ID       [%d]\n'%(self.table_id_extension)
        res = '\n'.join(resar)
        return res
    
'''UNIT TESTS -------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------------
'''
if __name__ == '__main__':
    print 'Testing Bat class'
    import unittest
    import _known_tables
    
    sample_bat = _known_tables.get_sample_bat_data()[0]
    
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
        known_sections = {testBatSection:sample_bat}

        def testKnownSections(self):
            for function in self.known_sections:
                data = self.known_sections[function]
                bat = Bat(data)
                print bat.get_service_list(5)
                print bat
                function(self, bat)

    unittest.main()


        
    