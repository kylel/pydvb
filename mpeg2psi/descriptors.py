"""MPEG2PSI Descriptors Module

MPEG2PSI Descriptors Module
"""
AUDIO_TYPE_STRINGS = {0x00:'Undefined',
                      0x01:'Clean effects',
                      0x02:'Hearing impaired',
                      0x03:'Visual impaired commentary'}

def add_descriptor_class(DescriptorClass):
    """Add a descriptor class to the descriptors table
    
    Add a descriptor class to the descriptors table so that get_descriptors() is able
    to use it
    """
    if DescriptorClass.tag in DESC_TABLE: return
    DESC_TABLE[DescriptorClass.tag] = DescriptorClass

def get_descriptors(data):
    """Returns a list of descriptor objects from the given data
    
    Parses the given data and instantiates descriptors objects to describe each descriptor
    represented in the data. For each descriptor it will search through DESC_TABLE and
    instantiate a descriptor class based on the tag in the first data byte. 
    Arguments:
        data -- a list of data bytes
    Returns:
        A list of Descriptor objects
    """
    descriptors = []
    ln = len(data)
    offset = 0
    while ln > 0:
        data = data[offset:offset+ln]
        if data[0] in DESC_TABLE:
            desc = DESC_TABLE[data[0]](data)
        else:
            #print '\n\nDescriptor with tag 0x%x is not yet implemented\n\n'%(data[0])
            desc = Descriptor(data)
        ln -= desc.length
        offset = desc.length
        descriptors.append(desc)
    return descriptors

class Descriptor(object):
    """MPEG2 PSI Descriptor class
    
    MPEG2 PSI Descriptors have a basic format. Given a block of data that has a descriptor in it,
    the first byte is the descriptor tag and the second byte is the descriptor length. The
    remaining bytes (for the length of the descriptor) are the descriptor data. This class
    is able to parse a data black and find the descriptor tag and length.
    """
    tag = None 

    def __init__(self, data):
        """Constructor
        
        Parses the given descriptor data and finds the descriptor length and tag which are saved
        as instance of the new instance.
        """
        self.descriptor_tag = self.__class__.tag
        if self.descriptor_tag == None:
            self.descriptor_tag = data[0]
        self.parse(data)
    
    def parse(self, data):
        """Parse the given data to get descriptor information
        
        Parses the given descriptor data and finds the descriptor length and tag which are saved
        as instance members.
        """
        #TODO - Add a tag check for sanity?
        self.descriptor_length = data[1]
        self.length = self.descriptor_length + 2
    
    def __str__(self):
        res = 'Descriptor:\n'
        res += '\ttag    = [0x%x]\n'%(self.descriptor_tag)
        res += '\tlength = [%d]\n'%(self.descriptor_length)
        return res 

class ConditionalAccessDescriptor(Descriptor):
    """Conditional Access Descriptor class
    
    Normally found in CATs or PMTs. Holds information about CA PIDs in the program. This class
    inherits from Descriptor and can be instantiated using descriptor data from a section
    """
    tag = 0x09
    def __init__(self, data):
        """Constructor
        
        Creates the descriptor from the given data by calling ConditionalAccessDescriptor.parse().
        """
        self.ca_system_id = None
        self.ca_pid = None
        super(ConditionalAccessDescriptor, self).__init__(data)
    
    def parse(self, data):
        """Parse the given data to get descriptor information
        
        Parses the given descriptor data and finds CA system ID and the CA PID. It also saves
        the descriptor private data in a list.
        """
        super(ConditionalAccessDescriptor, self).parse(data)
        self.ca_system_id = (data[2] << 8) + data[3]
        self.ca_pid = (data[4] & int('00011111', 2)) << 8
        self.ca_pid += data[5]
        self.private_data = data[6:self.length]
                
    def __str__(self):
        res = 'ConditionalAccessDescriptor:\n'
        res += '\tca system id = [0x%x]\n'%(self.ca_system_id)
        res += '\tca pid = [0x%x]\n'%(self.ca_pid)
        for byte in self.private_data:
            res += '[0x%x]'%(byte)
        res+='\n'
        return res

class Iso639LanguageDescriptor(Descriptor):
    """ISO639 Language Descriptor class
    
    Normally found the PMT. Holds information about the language of the audio tracks in
    a program.
    """
    tag = 0x0a
    def __init__(self, data):
        """Constructor
        
        Creates the descriptor from the given data by calling Iso639LanguageDescriptor.parse().
        """
        self.audio_streams = {}
        super(Iso639LanguageDescriptor, self).__init__(data)
    
    def parse(self, data):
        """Parse the given data to get descriptor information
        
        Parses the given descriptor data and finds a list of audio streams with languages and types.
        These are all saved in a local dictionary.
        """
        super(Iso639LanguageDescriptor, self).parse(data)
        ln = self.descriptor_length
        offset = 2
        while ln > 0:
            language = ''.join([chr(x) for x in data[offset:offset+3]])
            type = data[offset+3]
            self.audio_streams[language] = type
            ln -= 4
            offset += 4
    
    def __str__(self):
        res = 'Iso639LanguageDescriptor:\n'
        for language in self.audio_streams:
            type = AUDIO_TYPE_STRINGS.get(self.audio_streams[language], 'Reserved')
            res += '\tlanguage[%s] -> type[%s]\n'%(language, type)
        return res

DESC_TABLE = {
ConditionalAccessDescriptor.tag :ConditionalAccessDescriptor,
Iso639LanguageDescriptor.tag    :Iso639LanguageDescriptor
}