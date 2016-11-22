import StringIO
from twisted.trial import unittest
from twisted.python import log
import unittest

from opennsa import nsa
from opennsa.backends import junos
from opennsa.topology import nml
from opennsa.topology import nrm
import sys


class CommandGeneratorTest(unittest.TestCase):
    
#    log.startLogging(sys.stdout)
    maxDiff = None

    junos_routers = { 
                "junoslight"  :   "10.1.1.1",
                "junoslight2" :   "10.1.1.2",
                "netherlight":  "10.1.1.3",
                }

    def getTopologyPortMap(self):
        NRM_ENTRY = \
        """
        # some comment
        ethernet     local_vl1       -                               vlan:9-15      1000    ge1/1/2     -
        ethernet     local_vl2       -                               vlan:9-15      1000    ge1/0/2     -
        ethernet     local_eth1      -                               -            1000    ge1/1/1     -
        ethernet     local_eth2      -                               -            1000    ge1/0/1     -
        ethernet     netherlight        netherlight#junoslight-(in|out)   mpls:1-1000            1000    xe1     -
        ethernet     junoslight2       junoslight2#junoslight-(in|out)  mpls:1-1000            1000    xe2     -
        ethernet     junoslight3       junoslight3#junoslight-(in|out)  vlan:200-2500            1000    ge1/2/1     -
        ethernet     junoslight4       junoslight4#junoslight-(in|out)  -            1000    ge1/2/2     -
        """
        
        nrm_ports = nrm.parsePortSpec( StringIO.StringIO(NRM_ENTRY) )
        
        port_map = dict( [ (p.name,p) for p in nrm_ports ] ) 
        
        

        return port_map

    def getTopologyJUNOSTargetMap(self):
        port_map = self.getTopologyPortMap()
        
#        for name,p in port_map.iteritems():
#            log.msg("Port map iter %s -> %s %s" % (name, p, "" if p.label == None else p.label.type_))
        junosTarget_map = dict()
        for p,port in port_map.iteritems():
            if port.label is not None and (  port.label.type_ == 'vlan' or port.label.type_ == "mpls") :
                log.msg("%s = %s " % (port.label.type_,port.label.values))
                for vlan_range in port.label.values:
                    for vlan in range(vlan_range[0],vlan_range[1]+1):
                        junosTarget_map[p+"-"+str(vlan)] = junos.JUNOSTarget(port,p,vlan)
#                        log.msg("%s -> %s " % ((p+'-'+str(vlan)),"a"))
            else:
                junosTarget_map[p] = junos.JUNOSTarget(port,p)
                log.msg("%s = %s " % (p,junosTarget_map[p]))

        return junosTarget_map

    # Local port-port connection
    def testGenerateLocalPortPortConnectionActivateCommands(self):
        junosTarget_map = self.getTopologyJUNOSTargetMap()
        src_target = junosTarget_map['local_eth1']
        dst_target = junosTarget_map['local_eth2']
        expectedCommands    = [ 
                "set interfaces ge1/1/1 encapsulation ethernet-ccc",
                "set interfaces ge1/1/1 mtu 9000",
                "set interfaces ge1/1/1 unit 0 family ccc",
                "set interfaces ge1/0/1 encapsulation ethernet-ccc",
                "set interfaces ge1/0/1 mtu 9000",
                "set interfaces ge1/0/1 unit 0 family ccc",
                "set protocols connections interface-switch JUNOS-local-randomConId interface ge1/1/1.0",
                "set protocols connections interface-switch JUNOS-local-randomConId interface ge1/0/1.0"
        ]
        cg = junos.JUNOSCommandGenerator("randomConId",src_target,dst_target,self.junos_routers,"junoslight")
        generatedCommands = cg.generateActivateCommand() 
        log.msg("\n".join(generatedCommands))
        self.assertSequenceEqual(generatedCommands,expectedCommands)
        log.msg("\n".join(generatedCommands))
    # Local port-port connection
    def testGenerateLocalPortPortConnectionDeActivateCommands(self):
        junosTarget_map = self.getTopologyJUNOSTargetMap()
        src_target = junosTarget_map['local_eth1']
        dst_target = junosTarget_map['local_eth2']
        expectedCommands    = [ 
                "delete interfaces ge1/1/1",
                "delete interfaces ge1/0/1",
                "delete protocols connections interface-switch JUNOS-local-randomConId"
        ]
        cg = junos.JUNOSCommandGenerator("randomConId",src_target,dst_target,self.junos_routers,"junoslight")
        generatedCommands = cg.generateDeactivateCommand() 
        log.msg("\n".join(generatedCommands))

        self.assertSequenceEqual(generatedCommands,expectedCommands)
        log.msg("\n".join(generatedCommands))

 
    # Test local vlan-vlan connection
    def testGenerateLocalVlanVlanConnectionActivateCommands(self):
        junosTarget_map = self.getTopologyJUNOSTargetMap()
        src_target = junosTarget_map['local_vl1-10']
        dst_target = junosTarget_map['local_vl2-11']
        expectedCommands    = [ 
                "set interfaces ge1/1/2 flexible-vlan-tagging",
                "set interfaces ge1/1/2 encapsulation flexible-ethernet-services",
                "set interfaces ge1/1/2 unit 10 encapsulation vlan-ccc",
                "set interfaces ge1/1/2 unit 10 vlan-id 10",
                "set interfaces ge1/1/2 unit 10 input-vlan-map pop",
                "set interfaces ge1/1/2 unit 10 output-vlan-map push",
                "set interfaces ge1/0/2 flexible-vlan-tagging",
                "set interfaces ge1/0/2 encapsulation flexible-ethernet-services",
                "set interfaces ge1/0/2 unit 11 encapsulation vlan-ccc",
                "set interfaces ge1/0/2 unit 11 vlan-id 11",
                "set interfaces ge1/0/2 unit 11 input-vlan-map pop",
                "set interfaces ge1/0/2 unit 11 output-vlan-map push",
                "set protocols connections interface-switch JUNOS-local-randomConId interface ge1/1/2.10",
                "set protocols connections interface-switch JUNOS-local-randomConId interface ge1/0/2.11"
        ]
        cg = junos.JUNOSCommandGenerator("randomConId",src_target,dst_target,self.junos_routers,"junoslight")
        generatedCommands = cg.generateActivateCommand() 
        log.msg("\n".join(generatedCommands))
        self.assertSequenceEqual(generatedCommands,expectedCommands)

    # Local vlan-vlan connection
    def testGenerateLocalVlanVlanConnectionDeActivateCommands(self):
        junosTarget_map = self.getTopologyJUNOSTargetMap()
        src_target = junosTarget_map['local_vl1-10']
        dst_target = junosTarget_map['local_vl2-11']
        expectedCommands    = [ 
                "delete interfaces ge1/1/2.10",
                "delete interfaces ge1/0/2.11",
                "delete protocols connections interface-switch JUNOS-local-randomConId"
        ]
        cg = junos.JUNOSCommandGenerator("randomConId",src_target,dst_target,self.junos_routers,"junoslight")
        generatedCommands = cg.generateDeactivateCommand() 
        self.assertSequenceEqual(generatedCommands,expectedCommands)
    


    # Test local vlan-port connection
    def testGenerateLocalPortVlanConnectionActivateCommands(self):
        junosTarget_map = self.getTopologyJUNOSTargetMap()
        src_target = junosTarget_map['local_eth1']
        dst_target = junosTarget_map['local_vl2-13']
        expectedCommands    = [ 
                "set interfaces ge1/1/1 encapsulation ethernet-ccc",
                "set interfaces ge1/1/1 mtu 9000",
                "set interfaces ge1/1/1 unit 0 family ccc",
                "set interfaces ge1/0/2 flexible-vlan-tagging",
                "set interfaces ge1/0/2 encapsulation flexible-ethernet-services",
                "set interfaces ge1/0/2 unit 13 encapsulation vlan-ccc",
                "set interfaces ge1/0/2 unit 13 vlan-id 13",
                "set interfaces ge1/0/2 unit 13 input-vlan-map pop",
                "set interfaces ge1/0/2 unit 13 output-vlan-map push",
                "set protocols connections interface-switch JUNOS-local-randomConId interface ge1/1/1.0",
                "set protocols connections interface-switch JUNOS-local-randomConId interface ge1/0/2.13"
        ]
        cg = junos.JUNOSCommandGenerator("randomConId",src_target,dst_target,self.junos_routers,"junoslight")
        generatedCommands = cg.generateActivateCommand() 
        log.msg("\n".join(generatedCommands))
        self.assertSequenceEqual(generatedCommands,expectedCommands)

    # local vlan-port connection
    def testGenerateLocalPortVlanConnectionDeActivateCommands(self):
        junosTarget_map = self.getTopologyJUNOSTargetMap()
        src_target = junosTarget_map['local_eth1']
        dst_target = junosTarget_map['local_vl2-13']
        expectedCommands    = [ 
                "delete interfaces ge1/1/1",
                "delete interfaces ge1/0/2.13",
                "delete protocols connections interface-switch JUNOS-local-randomConId"
        ]
        cg = junos.JUNOSCommandGenerator("randomConId",src_target,dst_target,self.junos_routers,"junoslight")
        generatedCommands = cg.generateDeactivateCommand() 
        self.assertSequenceEqual(generatedCommands,expectedCommands)
   

    # Remote port connection over mpls
    def testGenerateRemotePortConnectionActivateCommands(self):
        junosTarget_map = self.getTopologyJUNOSTargetMap()
        src_target = junosTarget_map['netherlight-5']
        dst_target = junosTarget_map['local_eth1']
        expectedCommands    = [ 
                "set interfaces ge1/1/1 encapsulation ethernet-ccc",
                "set interfaces ge1/1/1 mtu 9000",
                "set interfaces ge1/1/1 unit 0 family ccc",
                "set protocols mpls label-switched-path T-netherlight-F-junoslight-mpls5 to 10.1.1.3",
                "set protocols mpls label-switched-path T-netherlight-F-junoslight-mpls5 no-cspf",
                "set protocols connections remote-interface-switch randomConId interface ge1/1/1",
                "set protocols connections remote-interface-switch randomConId transmit-lsp T-netherlight-F-junoslight-mpls5",
                "set protocols connections remote-interface-switch randomConId receive-lsp T-junoslight-F-netherlight-mpls5",
        ]
        cg = junos.JUNOSCommandGenerator("randomConId",src_target,dst_target,self.junos_routers,"junoslight")
        generatedCommands = cg.generateActivateCommand() 
        log.msg("\n".join(generatedCommands))
        self.assertSequenceEqual(generatedCommands,expectedCommands)
 
    # Remote port connection over mpls
    def testGenerateRemotePortConnectionDeActivateCommands(self):
        junosTarget_map = self.getTopologyJUNOSTargetMap()
        src_target = junosTarget_map['netherlight-8']
        dst_target = junosTarget_map['local_eth1']
        expectedCommands    = [ 
                "delete interfaces ge1/1/1",
                "delete protocols mpls label-switched-path T-netherlight-F-junoslight-mpls8",
                "delete protocols connections remote-interface-switch randomConId",
        ]
        cg = junos.JUNOSCommandGenerator("randomConId",src_target,dst_target,self.junos_routers,"junoslight")
        generatedCommands = cg.generateDeactivateCommand() 
        log.msg("\n".join(generatedCommands))
        self.assertSequenceEqual(generatedCommands,expectedCommands)



    # Remote vlan connection over MPLS
    def testGenerateRemoteVlanConnectionOverMplsActivateCommands(self):
        junosTarget_map = self.getTopologyJUNOSTargetMap()
        src_target = junosTarget_map['netherlight-11']
        dst_target = junosTarget_map['local_vl2-13']
        expectedCommands    = [ 
                "set interfaces ge1/0/2 flexible-vlan-tagging",
                "set interfaces ge1/0/2 encapsulation flexible-ethernet-services",
                "set interfaces ge1/0/2 unit 13 encapsulation vlan-ccc",
                "set interfaces ge1/0/2 unit 13 vlan-id 13",
                "set interfaces ge1/0/2 unit 13 input-vlan-map pop",
                "set interfaces ge1/0/2 unit 13 output-vlan-map push",
                "set protocols mpls label-switched-path T-netherlight-F-junoslight-mpls11 to 10.1.1.3",
                "set protocols mpls label-switched-path T-netherlight-F-junoslight-mpls11 no-cspf",
                "set protocols connections remote-interface-switch randomConId interface ge1/0/2.13",
                "set protocols connections remote-interface-switch randomConId transmit-lsp T-netherlight-F-junoslight-mpls11",
                "set protocols connections remote-interface-switch randomConId receive-lsp T-junoslight-F-netherlight-mpls11",
        ]
        cg = junos.JUNOSCommandGenerator("randomConId",src_target,dst_target,self.junos_routers,"junoslight")
        generatedCommands = cg.generateActivateCommand() 
        log.msg("\n".join(generatedCommands))
        self.assertSequenceEqual(generatedCommands,expectedCommands)
 
    # Remote vlan connection over MPLS
    def testGenerateRemoteVlanConnectionOverMplsDeActivateCommands(self):
        junosTarget_map = self.getTopologyJUNOSTargetMap()
        src_target = junosTarget_map['netherlight-55']
        dst_target = junosTarget_map['local_vl2-13']
        expectedCommands    = [ 
                "delete interfaces ge1/0/2.13",
                "delete protocols mpls label-switched-path T-netherlight-F-junoslight-mpls55",
                "delete protocols connections remote-interface-switch randomConId",
        ]
        cg = junos.JUNOSCommandGenerator("randomConId",src_target,dst_target,self.junos_routers,"junoslight")
        generatedCommands = cg.generateDeactivateCommand() 
        log.msg("\n".join(generatedCommands))
        self.assertSequenceEqual(generatedCommands,expectedCommands)
 
    # Remote vlan connection over Vlan
    def testGenerateRemoteVlanConnectionOverVlanActivateCommands(self):
        junosTarget_map = self.getTopologyJUNOSTargetMap()
        src_target = junosTarget_map['junoslight3-266']
        dst_target = junosTarget_map['local_vl2-13']
        expectedCommands    = [ 
                "set interfaces ge1/0/2 flexible-vlan-tagging",
                "set interfaces ge1/0/2 encapsulation flexible-ethernet-services",
                "set interfaces ge1/0/2 unit 13 encapsulation vlan-ccc",
                "set interfaces ge1/0/2 unit 13 vlan-id 13",
                "set interfaces ge1/0/2 unit 13 input-vlan-map pop",
                "set interfaces ge1/0/2 unit 13 output-vlan-map push",
                "set interfaces ge1/2/1 flexible-vlan-tagging",
                "set interfaces ge1/2/1 encapsulation flexible-ethernet-services",
                "set interfaces ge1/2/1 unit 266 encapsulation vlan-ccc",
                "set interfaces ge1/2/1 unit 266 vlan-id 266",
                "set interfaces ge1/2/1 unit 266 input-vlan-map pop",
                "set interfaces ge1/2/1 unit 266 output-vlan-map push",
                "set protocols connections interface-switch JUNOS-local-randomConId interface ge1/0/2.13",
                "set protocols connections interface-switch JUNOS-local-randomConId interface ge1/2/1.266"
                ]
        cg = junos.JUNOSCommandGenerator("randomConId",src_target,dst_target,self.junos_routers,"junoslight")
        generatedCommands = cg.generateActivateCommand() 
        log.msg("\n".join(generatedCommands))
        self.assertSequenceEqual(generatedCommands,expectedCommands)
 
    # Remote vlan connection over Vlan
    def testGenerateRemoteVlanConnectionOverVlanDeActivateCommands(self):
        junosTarget_map = self.getTopologyJUNOSTargetMap()
        src_target = junosTarget_map['junoslight3-266']
        dst_target = junosTarget_map['local_vl2-13']
        expectedCommands    = [ 
                "delete interfaces ge1/0/2.13",
                "delete interfaces ge1/2/1.266",
                "delete protocols connections interface-switch JUNOS-local-randomConId"
            ]
        cg = junos.JUNOSCommandGenerator("randomConId",src_target,dst_target,self.junos_routers,"junoslight")
        generatedCommands = cg.generateDeactivateCommand() 
        log.msg("\n".join(generatedCommands))
        self.assertSequenceEqual(generatedCommands,expectedCommands)

