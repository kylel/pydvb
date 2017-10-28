

class SiTable (object):
    """A basic SI TABLE class
    
    More
    """
    def __init__(self, tableid, tableid_ext=None):
        """Constructor
        
        More
        """
        self.tid  = tableid
        self.tide = tableid_ext
        self.cver = None
        self.complete = False
        self.table = {}
        pass
    
    def add_section(self, section):
        print section
        if section.table_id != self.tid: return
        tide = section.table_id_extension
        if self.tide != None:
            if self.tide != tide: return
        #section seems correct
        if section.version != self.cver:
            #new version
            self.table = {}
            self.cver   = section.version
            self.complete = False
        if self.complete: return
        if section.section_number not in self.table:
            self.table[section.section_number] = section
            if len(self.table) > section.last_section_number:
                self.complete = True
        #print self.table
        return

    def get_sections(self):
        return self.table
    
    def __str__(self):
        res  = 'SI TABLE:\n'
        res += '\ttable id           = [0x%x]\n'%(self.tid)
        if self.tide != None:
            res += '\ttable id extension = [0x%x]\n'%(self.tide)
        res += '\ttable version      = [0x%x]\n'%(self.cver)
        if self.complete:
            res += '\tCOMPLETE - all sections have been gathered\n'
        else:
            res += '\tINCOMPLETE - still missing sections\n'
        res += '\tSECTIONS:----------------------------------------\n'
        for sect in self.table:
            res += str(self.table[sect])
        res += '\tEND OF TABLE:------------------------------------\n'
        return res
    
'''UNIT TESTS -------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------------
'''
if __name__ == '__main__':
    print 'Testing SI TABLE class'
    #TODO - not a full unit test - need to do partial data addition
    import unittest
    import _known_tables

    nit_0 = _known_tables.get_sample_nit_sections()[0]
    nit_1 = _known_tables.get_sample_nit_sections()[1]
    
    class KnownSections(unittest.TestCase):
                
        def testKnownSections(self):
            nit = SiTable(64)
            self.assertEqual(nit.complete, False)
            nit.add_section(nit_0)
            self.assertEqual(nit.complete, False)
            self.assertEqual(nit.cver, 1)
            nit.add_section(nit_1)
            self.assertEqual(nit.complete, True)
            print nit                            
                
    unittest.main()