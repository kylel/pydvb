from mpeg2psi.section import Section, section_syntax_flag, get_version_number, get_section_number, get_table_id_extension
from mpeg2psi.section import get_table_id
from si_table import SiTable
import packet_tools as pct
from buffer import BufferReader

'''
class SectionBuilder(BufferReader):
    def __init__(self, buffer, section_class=Section):
        BufferReader.__init__(self, buffer)
        self.sections = {}
        self.current_sct = None
        self.sct_cls = section_class
        self.current_version =  None
        self.current_table = {}
        self.current_num_sections = 0

    def _loop(self):
        packet = self.buff.read()
        if packet == -1:
            self.halt = True
            return
        if packet == None: return
        psi = pct.payload_start_flag(packet)
        if psi:
            data = pct.get_payload(packet)
            offset = data[0] + 1
            section_data = data[offset:]
            if section_syntax_flag(section_data):
                section_version =  get_version_number(section_data)
                if section_version in self.sections:
                    #print 'already have this section version ', section_version
                    return
                print "dont have this version yet! ", section_version
                self.current_version =  section_version
                section_number = get_section_number(section_data)
                self.current_num_sections = get_last_section_number(section_data)
                if section_number in self.current_table:
                    #print 'already have this section number ', section_number
                    return
                print "dont have this number yet! ", section_number
                self.current_section_number = section_number
            self.current_sct = self.sct_cls(section_data)

        else:
            if not self.current_sct: return
            self.current_sct.add_data(pct.get_payload(packet))
        if self.current_sct.complete:
            self.current_table[self.current_section_number] = self.current_sct
            print self.current_table
            self.current_sct = None
            print "current len =" ,len(self.current_table)
            print "target len =", self.current_num_sections

            if len(self.current_table) == self.current_num_sections + 1:
                self.sections[self.current_version] = self.current_table
'''				






class SectionBuilder1(BufferReader):
    def __init__(self, buffer, section_class=Section):
        BufferReader.__init__(self, buffer)
        self.si_table = SiTable()
        self.current_sct = None
        self.sct_cls = section_class
        self.long_table = False
        self.sections = []

    def _loop(self):
        packet = self.buff.read()
        if packet == -1:
            self.halt = True
            return
        if packet == None: return
        psi = pct.payload_start_flag(packet)
        if psi:
            data = pct.get_payload(packet)
            offset = data[0] + 1
            section_data = data[offset:]

            if self.current_sct:
                if offset > 1: print "????????????????????????????"
                if (not self.current_sct.complete) and (offset > 1):
                    print "Found it"
                    self.current_sct.add_data(data[1:offset])
                    if self.current_sct.complete:
                        if self.long_table:
                            self.si_table.add_section(self.current_sct)
                        else:
                            self.sections.append(self.current_sct)
                        self.current_sct = None


            if section_syntax_flag(section_data):
                self.long_table = True
                section_version = get_version_number(section_data)
                section_number = get_section_number(section_data)
                if self.si_table.do_you_need(section_version, section_number):
                    self.current_sct = self.sct_cls(section_data)
                else: return
            else:
                self.current_sct = self.sct_cls(section_data)
                self.long_table = False

        else:
            if not self.current_sct: return
            self.current_sct.add_data(pct.get_payload(packet))
        if self.current_sct.complete:
            if self.long_table:
                self.si_table.add_section(self.current_sct)
            else:
                self.sections.append(self.current_sct)
            self.current_sct = None

STATE_WAITING_FOR_PSI = 0
STATE_BUILDING = 1


class SectionBuilder(BufferReader):
    def __init__(self, buffer, section_class=Section):
        super(SectionBuilder, self).__init__(buffer)
        self.current_sct = None
        self.sct_cls = section_class
        self.long_table = None
        self.state = STATE_WAITING_FOR_PSI

    def _loop(self):
        packet = self.buff.read()
        if packet == -1:
            self.halt = True
            return
        if packet == None: return
        psi = pct.payload_start_flag(packet)
        #print ("psi for this packet is %d"%(psi))
        data = pct.get_payload(packet)
        if self.state == STATE_WAITING_FOR_PSI:
            self.waiting_for_psi(data, psi)
        elif self.state == STATE_BUILDING:
            self.building(data, psi)

    def waiting_for_psi(self, data, psi):
        if psi:
            offset = data[0] + 1
            section_data = data[offset:]
            #print "[%d]got section version[%d], number[%d]"%(self.sct_cls.TABLE_ID, get_version_number(section_data), get_section_number(section_data))
            if self.long_table == None:
                if section_syntax_flag(section_data):
                    self.long_table = True
                    self.si_table = SiTable()
                else:
                    self.long_table = False
            self.process_new_section(section_data)
        else:
            return

    def building(self, data, psi):
        #print "building"
        if psi:
            print "\n\nPROBLEM, got psi while still building a section!!!!!\n\n"
            offset = data[0] + 1
            if offset > 1: #grab the data before the new section
                self.building(data[1:offset], False)
            section_data = data[offset:]
            self.process_new_section(section_data)
        else:
            #print "adding data (%d bytes)"%(len(data))
            added = self.current_sct.add_data(data)
            #print added
            #print "ADDED = %d"%(added)
            if self.current_sct.complete:
                self.save_current_section()
                if added < len(data):
                    print "residual data[%d]"%(len(data))
                    print "added[%d]"%(added)
                    if data[added] != 0xff:
                        self.process_new_section(data[added:])
                    else:
                        self.state = STATE_WAITING_FOR_PSI


    def process_new_section(self, data):
        if self.long_table:
            version = get_version_number(data)
            number  = get_section_number(data)
            tide    = get_table_id_extension(data)
            #print "new section - version[%d], num[%d]"%(version, number)
            tid = get_table_id(data)
            if tid != self.sct_cls.TABLE_ID:
                print("wrong table id")
                return
            if not self.si_table.do_you_need(version, tide, number):
                #print "dont need this table"
                return

        self.current_sct = self.sct_cls(data)
        if self.current_sct.complete:
            #print "section already complete"
            added = self.current_sct.length
            self.save_current_section()
            if added < len(data):
                #print "residual section with table id [%d]"%(data[added])
                if data[added] != 0xff:
                    #print "waiting for psi"
                    self.process_new_section(data[added:])
                else:
                    #print "waiting for psi"
                    self.state = STATE_WAITING_FOR_PSI
            else:
                #print "waiting for psi"
                self.state = STATE_WAITING_FOR_PSI
        else:
            print "building"
            self.state = STATE_BUILDING


    def save_current_section(self):
        if self.long_table:
            #print self.current_sct
            self.si_table.add_section(self.current_sct)
        else:
            #print "hello-" + str(self.current_sct)
            self.sections.append(self.current_sct)
        self.current_sct = None
