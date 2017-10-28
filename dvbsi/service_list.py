"""DVB Service List module

    Provides a ServiceList class to maintain a list of DVB services using DVB-SI tables
"""

class ServiceList(object):
    """Service List class
    
    Manages a list of Service objects. Allows the list to be updated by adding NIT,
    BAT or SDT Sections. A list of service objects will be maintained and updated
    when new table information is added.
    """
    def __init__(self):
        """Constructor
        
        Creates the ServiceLIst object
        """
        self.svl = {}
    
    def _add_service(self, service):
        """Add a service to the service list
    
            Adds a service to the service list
            Arguments:
               service -- dvbsi.Service object
        """
        trip = service.get_triplet()
        self.svl[trip] = service
    
    def _svl_sync(self, svlin, nid, tid):
        """Synchronises with the given service list for the given double
    
            Given a dictionary of services for a specific network and transport stream ID,
            this method will synchronise the the ServiceList to information in the given
            list of services. This includes adding missing items to the ServiceList and
            calling update on each service with the related item in the given list.
            Arguments:
               svlin -- the master dictionary to sync with
               nid   -- the network ID of all the services in the given list
               tid   -- the transport stream ID of all the services in the given list
        """
        for trip in self.svl:
            if trip in svlin:
                self.svl[trip].update(svlin[trip])
            else:
                tnid, ttid = trip[0], trip[1]
                if tnid==nid and ttid==tid:
                    #if the transport and network ID match those of the given list,
                    #then it is safe to say this service is no longer valid and
                    #should be removed
                    self.svl.pop(trip) 
        for trip in svlin:
            if trip not in self.svl:
                self._add_service(svlin[trip])
    
    def _svl_update(self, svlin):
        """Updates the ServiceList with information from the given list of services
    
            This private method will use a given service dictionary to update its instance's services.
            The given list will be parsed and if any services exist in it that are in
            this instances list, they will be used to update the service information. 
            For example, the service list is created with Information from the NIT TS loop.
            Then the SDT can be used to update names of all the services.
            Arguments:
               svlin -- the dictionary to update with
        """
        for trip in self.svl:
            if trip in svlin:
                self.svl[trip].update(svlin[trip])
    
    def _update_nit(self, nit):
        """Update the ServiceList with a NIT section
        
        Private method: Given a dvbsi.Nit object, this method will update the list services maintained in this
        ServiceList. NITs are used as the primary service list. The ServiceList will maintain a list of
        services that directly represents those in the NIT.
        Arguments:
            nit -- dvbsi.Nit object
        """
        nit_service_lists = nit.get_all_service_lists()
        for double in nit_service_lists:
            nid = double[0]
            tid = double[1]
            nsvl = nit_service_lists[double]
            #dict_sync(nsvl, self.svl)
            self._svl_sync(nsvl, nid, tid)
    
    def _update_bat(self, bat):
        """Update the ServiceList with a BAT section
        
        Private method: Given a dvbsi.Bat object, this method will update the list services maintained in this
        ServiceList. Information in the BATs is secondary to any information given in the NITs. The ServiceList
        will maintain a list of services that directly represents those in the NIT and only use BATs to
        supplement service information (eg. channel numbers)
        Arguments:
            bat -- dvbsi.Bat object
        """
        bat_service_lists = bat.get_all_service_lists()
        for double in bat_service_lists:
            bsvl = bat_service_lists[double]
            #dict_update(bsvl, self.svl)
            self._svl_update(bsvl)

    def _update_sdt(self, sdt):
        """Update the ServiceList with a SDT section
        
        Private method: Given a dvbsi.Sdt object, this method will update the list services maintained in this
        ServiceList. Information in the SDTs is secondary to any information given in the NITs. The ServiceList
        will maintain a list of services that directly represents those in the NIT and only use SDTs to
        supplement service information (eg. service names)
        Arguments:
            sdt -- dvbsi.Sdt object
        """
        ssvl = sdt.get_service_list()
        if ssvl == None: return
        #dict_update(ssvl, self.svl)
        self._svl_update(ssvl)
    
    def update(self, nit=None, bat=None, sdt=None):
        """Update the ServiceList with the given DVB-SI tables
        
        Gets service information from the given DVB-SI section tables and uses it to update and maintain the
        inner service list.
        Arguments:
            nit -- dvbsi.Nit object (default, None)
            bat -- dvbsi.Bat object (default, None)
            sdt -- dvbsi.Sdt object (default, None)
        """
        if nit: self._update_nit(nit)
        if bat: self._update_bat(bat) 
        if sdt: self._update_sdt(sdt)
    
    def get_service(self, identifier):
        """Get a service Object from the ServiceList
        
        Will search the service list for services with the given identifier. All services that have
        this identifier will be returned.
        Arguments:
            identifier -- could be the service ID or a DVB triplet in tuple format
        Returns
            A list of dvbsi.Service objects
        """
        services = []
        if type(identifier) == tuple:
            services.append(self.svl.get(identifier))
        else:
            service_id = identifier
            for triplet in self.svl:
                service = self.svl[triplet]
                if service.svid == service_id:
                    services.append(service)
        return services
    
    def get_service_count(self):
        """Get the number of services in the ServiceList
        
        Get the number of services in the ServiceList
        Returns
            The service count
        """
        return len(self.svl)

    def get_service_list(self, network_id, transport_id):
        """Get a list of services belonging to the given Network ID and Transport ID
        
        Search the service list and return a list of services that belong to the given
        Network and transport stream pair.
        Arguments:
            network_id   -- DVB Network ID
            transport_id -- DVB Transport Stream ID
        Returns:
            A dictionary of Service objects keyed by DVB triple
        """
        svl = {}
        for trip in self.svl:
            nid, tid = trip[0], trip[1]
            if (nid, tid) == (network_id, transport_id):
                svl[trip] = self.svl[trip]
        return svl

    def get_doubles(self):
        """Get a list of DVB doubles described in this service list
        
        Search the service list and return a list doubles (Network ID, TS ID) described in the list.
        Returns:
            A list of doubles in tuple format (Network ID, Transport ID)
        """
        doubles = []
        for trip in self.svl:
            nid, tid = trip[0], trip[1]
            doubles.append((nid,tid))
        doubles = list(set(doubles))
        return doubles
        
    
    def __str__(self):
        res = "service list:\n"
        for svc in self.svl:
            res += str(self.svl[svc])
            res += '\n'
        return res    

'''UNIT TESTS -------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------------
'''
if __name__ == '__main__':
    print 'Testing ServiceList class'
    import unittest
    import _known_tables
    
    sample_nit_0 = _known_tables.get_sample_nit_sections()[0]
    sample_nit_1 = _known_tables.get_sample_nit_sections()[1]
    sample_bat   = _known_tables.get_sample_bat_sections()[0]
    sample_sdt   = _known_tables.get_sample_sdt_sections()[0]
    
    class KnownSections(unittest.TestCase):
        def testKnownSections(self):
            svl = ServiceList()
            print svl
            svl.update(nit=sample_nit_0)
            print svl.get_service_count()
            self.assertEqual(svl.get_service_count(), 259, 'incorrect service count')
            svl.update(bat=sample_bat)
            print svl.get_service_count()
            self.assertEqual(svl.get_service_count(), 259, 'incorrect service count')
            svl.update(nit=sample_nit_1)
            print svl.get_service_count()
            self.assertEqual(svl.get_service_count(), 282, 'incorrect service count')
            svl.update(sdt=sample_sdt)
            print svl.get_service_count()
            self.assertEqual(svl.get_service_count(), 282, 'incorrect service count')
            print svl
            service = svl.get_service((0x1800, 0x10, 0x67b))
            self.assertEqual(len(service), 1, 'incorrect number of services found')
            print service[0]
            service = service[0]
            self.assertEqual(service.get_triplet(), (0x1800, 0x10, 0x67b), 'incorrect service found')
            self.assertEqual(service.name, 'PVOD', 'incorrect service name')
            
            service = svl.get_service(0x67b)
            self.assertEqual(len(service), 1, 'incorrect number of services found')
            print service[0]
            service = service[0]
            self.assertEqual(service.get_triplet(), (0x1800, 0x10, 0x67b), 'incorrect service found')
            self.assertEqual(service.name, 'PVOD', 'incorrect service name')
            print svl.get_doubles()
            
            
    unittest.main()        