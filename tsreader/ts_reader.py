'''
    An example tool for reading a file from the HDD and processing the DVB info inside.
    You will need your own TS file to test with.
'''

from buffer import Buffer
import struct
import time
import threading
import packet_tools
import adaptation_field_tools
import section_builder
from dvbsi.nit import Nit
from mpeg2psi.pat import Pat
from dvbsi.bat import Bat
from dvbsi.sdt import Sdt
from mpeg2psi.cat import Cat
from mpeg2psi.pmt import Pmt
import dvbsi.service_list as service_list


class TsReader(threading.Thread):
    sync_byte = 0x47
    def __init__(self, file):
        self.file = file
        self.input = None
        self.links = {}
        self.pids  = {}
        threading.Thread.__init__(self)#super(TsReader, self).__init__()#

    def __str__(self):
        res = ''
        for pid in self.pids:
            res = res + "pid " + hex(pid) + " occurs " + str(self.pids[pid]) + " times\n"
        return res

    def link(self, pid, buffer):
        if pid not in self.links:
            self.links[pid] = []
        self.links[pid].append(buffer)
        buffer.link()

    def unlink(self, pid):
        pass

    def run(self):
        self.input = open(self.file, 'rb')
        self.stop = False
        self.loop()

    def stop(self):
        self.stop = True
        self.input.close()

    def loop(self):
        last_pcr = 0
        while not self.stop and self.input:
            packt_data = self.input.read(188) # read a packet
            if len(packt_data) < 188: break
            packet = struct.unpack('188B', packt_data)
            pid = packet_tools.get_pid(packet)
            if pid in self.links:
                for buffer in self.links[pid]:
                    buffer.write(packet)
            if pid not in self.pids:
                self.pids[pid] = 0
                print "new pid: ", hex(pid), "-- total = ", len(self.pids)
            self.pids[pid] = self.pids[pid] + 1
            af = packet_tools.get_adaptation_field(packet)
            if af == packet_tools.AF_ADAPTATION_FIELD_ONLY or af == packet_tools.AF_AF_AND_PL:
                #print 'af'
                #if adaptation_field_tools.opcr_flag(packet):
            #		print adaptation_field_tools.get_opcr(packet)
                if adaptation_field_tools.pcr_flag(packet):
                    pcr = adaptation_field_tools.get_pcr(packet)
                    #print pcr
                    ms =  pcr.to_micro_seconds()
                    #print '%d micro_seconds'%(ms)
                    delta = ms - last_pcr
                    #print '%d ms delta between pcrs'%(delta/1000)
                    last_pcr = ms

        for pid in self.links:
            for buffer in self.links[pid]:
                buffer.unlink()

    def sync(self): # sync after 5 x 0x47 -- lose sync after 3 non 0x47
        while True:
            byte = struct.unpack('1B', self.input.read(1))
            if byte == TsReader.sync_byte: break
        self.input.seek(-1, 1)


if __name__ == '__main__':
    t1 = time.time()
    dmx = TsReader('Your-ts-file-name-here.ts')
    buf = Buffer(188*10000)
    dmx.link(0x10, buf)
    buf2 = Buffer(188*10000)
    dmx.link(0x0, buf2)
    buf3 = Buffer(188*10000)
    dmx.link(0x11, buf3)
    buf4 = Buffer(188*10000)
    dmx.link(0x11, buf4)
    buf5 = Buffer(188*10000)
    dmx.link(0x01, buf5)

    buf6 = Buffer(188*1000)
    dmx.link(0x07f2, buf6)


    #nit = section_builder.SectionBuilder(buf, Nit)
    pat = section_builder.SectionBuilder(buf2, Pat)
    #bat = section_builder.SectionBuilder(buf3, Bat)
    #sdt = section_builder.SectionBuilder(buf4, Sdt)
    #cat = section_builder.SectionBuilder(buf5, Cat)
    pmt = section_builder.SectionBuilder(buf6, Pmt)
    dmx.start()
    #nit.start()
    pat.start()
    #bat.start()
    #sdt.start()
    #cat.start()
    pmt.start()


    res = dmx.join()
    #nit.join()
    pat.join()
    pmt.join()

    #print nit.si_table
    #print bat.si_table
    #print sdt.si_table
    #print cat.si_table
    print pat.si_table
    print pmt.si_table

    """
    msvl = service_list.Msvl([(6144, 16), (6144,11)])

    for version in nit.si_table.sections:
        for tide in nit.si_table.sections[version]:
            for number in nit.si_table.sections[version][tide]:
                table = nit.si_table.sections[version][tide][number]
                msvl.update(nit=table)

    for version in nit.si_table.sections:
        for tide in bat.si_table.sections[version]:
            for number in bat.si_table.sections[version][tide]:
                table = bat.si_table.sections[version][tide][number]
                if tide == 13858: print (table.get_bouquet_list())
                msvl.update(bat=table)

    for version in sdt.si_table.sections:
        for tide in sdt.si_table.sections[version]:
            for number in sdt.si_table.sections[version][tide]:
                table = sdt.si_table.sections[version][tide][number]
                msvl.update(sdt=table)

    for version in cat.si_table.sections:
        for tide in cat.si_table.sections[version]:
            for number in cat.si_table.sections[version][tide]:
                table = cat.si_table.sections[version][tide][number]
                msvl.update(cat=table)

    msvl.assign_ips('239.251.251.0', 1234)
    #print msvl
    msvl.update_file()

    print msvl.generate_html_selection_page()
    #print msvl
"""
    #print res
    print dmx

    t2 = time.time()
    print 'took %0.3f ms' % ((t2 - t1)* 1000.0)
    #print sdt.si_table.sections[1][0].get_service_name(0x65e)
    #print bat.si_table.sections[1][0].get_channel_number(0x65e)

