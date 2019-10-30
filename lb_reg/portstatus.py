import json
import random
import serial
from serialcom import SerialPort

class PortData():
    def __init__(self, port, BaseAddress):
        self.port = port
        self.BaseAddress = BaseAddress
        self.PortAddress = {'A': 0x40, 'B': 0x80, 'C': 0xc0, 'D': 0x100, 'E': 0x140}[port] + BaseAddress
        print((hex(self.PortAddress)))
        
    def activity(self, s):
        status = {}
        data = int(s.read_reg32(self.PortAddress),16)
        active = 'yes' if data & 0x1000 else 'no'
        lock   = 'no' if data & 0x100  else 'yes'
        sfp    = 'no' if data & 0x10   else 'yes'
        rate   = {0: '10G',1: 'na',2:'1G',3:'na',4:'2.5G',5:'5G',6:'na',7:'na'}[data & 0x07]
        averate  = "%d" % int(s.read_reg32(self.PortAddress+4),16)
        avedelay = "%d" % (int(s.read_reg32(self.PortAddress+0xc),16)*2)
        dropped  = "%d" % int(s.read_reg32(self.PortAddress+8),16)
       
        status = {self.port: {'active': active,'lock': lock, 'sfp': sfp,'rate':rate,'averate':averate,'avedelay':avedelay,'dropped':dropped}}
        return status
        
class PortStatus():
    def __init__(self,baseaddress):
        
        self.portA = PortData('A', baseaddress)
        self.portB = PortData('B', baseaddress)
        self.portC = PortData('C', baseaddress)
        self.portD = PortData('D', baseaddress)
        self.portE = PortData('E', baseaddress)
        
        
    def ps_json(self, s):
        ps = self.portA.activity( s)
        ps.update(self.portB.activity( s))
        ps.update(self.portE.activity( s))
        ps.update(self.portD.activity( s))
        ps.update(self.portC.activity( s))
        return json.dumps(ps)


#ps = PortStatus(0x60000000)
#print ps.ps_json()
