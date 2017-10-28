"""DVB Service module

    Provides a Service class to represent and hold information about a single DVB Service.
"""

from descriptors import SERVICE_TYPE_STRINGS

class Service(object):
    """Service class
    
    Holds information about a single DVBSI service.
    """
    def __init__(self, **kwargs):
        """Constructor
        
        Arguments:
            kwargs -- A dictionary of key word arguments. The following keys are relevant:
                nid  -- the network ID of the service
                tsid -- the transport stream ID
                svid -- the service ID
                chan -- the channel number
                name -- the service name
                type -- the service type
            And the constructor can be called with any or none of these arguments as they
            can be set at a later stage.
        """
        self.nid   = kwargs.pop('nid', None)
        self.tsid  = kwargs.pop('tsid', None)
        self.svid  = kwargs.pop('svid', None)
        self.chan  = kwargs.pop('chan', None)
        self.name  = kwargs.pop('name', None)
        self.type  = kwargs.pop('type', None)
        self.number = None

    def get_triplet(self):
        """Get the service DVB locator triplet

        Gets the DVB triplet (network ID, transport ID, service ID) for this service.
        Returns:
            The service DVB triplet in tuple form
        """  
        return self.nid, self.tsid, self.svid
    
    def get_unique_identifier(self):
        """Get a unique hash-able identifier for this Service

        Returns a unique identifier for this Service that can be used as a dictionary key. At
        the time of implementation this method uses the DVB triplet as a tuple. However, this
        may change. All that is guaranteed is that the identifier is unique and can be used
        as a dictionary key.
        Returns:
            Unique hash-able object
        """  
        return self.get_triplet()
    
    def update(self, other):
        """Use the given Service to update the attributes of this Service

        Use all the set attributes of the given Service to update this Service. Used in the case where
        you have created two Services from different sources that represent the same DVB service. Since
        they are from different sources each may contain different attributes. This method allows the
        given service to be updated with new information from another service.
        Arguments:
            other -- Another service to use for the update
        """ 
        for key in self.__dict__:
            attribute = other.__dict__.get(key, self.__dict__[key])
            if attribute == None: continue
            self.__dict__[key] = attribute

    def __eq__(self, other):
        """Equality operator overload

        Checks if the given service is equivalent. Will override the '==' operator. Two services are
        considered equal if they share the same triplet.
        Arguments:
            other -- Another service to equate to this one
        """
        if self.nid  != other.nid : return False
        if self.tsid != other.tsid: return False       
        if self.svid != other.svid: return False
        return True
    
    def __neq__(self, other):
        """Non-Equality operator overload

        Checks if the given service is different. Will override the '!=' operator. Two services are
        considered equal if they share the same triplet.
        Arguments:
            other -- Another service to equate to this one
        """
        return not self == other
        
    def __str__(self):
        nid, tsid, pn = self.nid, self.tsid, self.svid
        res =  'service:\n'
        if self.nid != None: 
            if self.tsid != None:
                if self.svid != None:
                    res += 'locator=dvb://%x.%x.%x\n'%(nid, tsid, pn)
        if self.chan: res += 'channel_number=%d\n'%(self.chan)
        if self.name: res += 'name=%s\n'%(self.name)
        if self.number: res += 'number=%s\n'%(self.number)
        if self.type:
            type = '%d'%(self.type)
            if self.type in SERVICE_TYPE_STRINGS:
                type = SERVICE_TYPE_STRINGS[self.type]
            res += 'type=%s\n'%(type)
        return res

'''UNIT TESTS -------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------------
'''
if __name__ == '__main__':
    svc = Service(nid=10, tsid=101, svid=10101, chan=5, name='test', type=1)
    svc2 = Service(nid=11, svid=11111, chan=6, name='test1', type=2)
    print svc
    svc.update(svc2)
    print svc
