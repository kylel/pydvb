'''
Section Tables come in parts. This is a tool to manage the acquisition of those parts
'''

class SiTable(object):
    def __init__(self):
        self.sections = {}
    
    def do_you_need(self, version, table_id_extension, section_number):
        if version in self.sections:
            if table_id_extension in self.sections[version]:
                if section_number in self.sections[version][table_id_extension]:
                    return False
        return True
    
    def add_section(self, section):
        version  = section.version
        number   = section.section_number
        tide     = section.table_id_extension 
        #print "new section added version[%d] number[%d]"%(version, number)
        if version in self.sections:
            if tide in self.sections[version]:
                if number in self.sections[version][tide]:
                    return
            else:
                self.sections[version][tide] = {}
        else:
            self.sections[version]       = {}        
            self.sections[version][tide] = {}
        self.sections[version][tide][number] = section
        #print section
        #print section.get_ca_pids()
        
    def __str__(self):
        res = 'SI Table:-----\n'
        for version in self.sections:
            res += 'Version [%d]\n'%(version)
            for tide in self.sections[version]:
                res += 'table id extension [%d]\n'%(tide)
                for number in self.sections[version][tide]:
                    res += 'Number [%d]\n'%(number)
                    res += str(self.sections[version][tide][number])
        res += 'SI Table:-----DONE'
        return res