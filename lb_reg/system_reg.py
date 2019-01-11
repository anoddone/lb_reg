import types
import logging
from serialcom import SerialPort


class systemReg():
    def __init__(self, BaseAddress = 0xff200000):
        self.log = logging.getLogger(self.__class__.__name__)
        self.BaseAddress = BaseAddress
        self.offset = {
        "a_portstatus": 0x0000,
        "b_portstatus": 0x0004,
        "c_portstatus": 0x0008,
        "d_portstatus": 0x000c,
        "e_portstatus": 0x0010,
        "redundancy":   0x0014,
      
        "fcnt25":       (0x001c,"%d"),
        "fcnt125":      (0x0020,"%d"),
        "fcnt156_25":   (0x0024,"%d"),
        "fcnt200":      (0x0028,"%d"),
        "fcnt312_5":    (0x002c,"%d"),
        "fcnt322_25":   (0x0030,"%d"),
        "date_code":    (0x0034,self.playdate),
        "temperature":  (0x0190,"%d F"),
        }
    
    def playdate(self, s, offset):
            val = s.read_reg32(offset)
            return "%sy %sm %sd %srev" %(val[0:2],val[2:4],val[4:6],val[6:8])
 
           
    def read_reg(self, s, name):
        offset = self.offset.get(name,None)
        if offset == None:
            self.log.error("reg offset not found: " + name)
            return None
        if type(offset) is int:
            return s.read_reg32(self.BaseAddress+offset)
        if type(offset) is tuple:
            if isinstance(offset[1],(types.MethodType,types.FunctionType)):
                self.s = s
                return offset[1](s,self.BaseAddress+offset[0])
            val = int(s.read_reg32(self.BaseAddress+offset[0]),16)
            rtnval = offset[1] % val
            rtnval = rtnval.replace(" ","&nbsp;")
            return rtnval

    def read_reg_dict(self, s, name):
        data = self.read_reg(s, name)
        if data:
            return {name : data}
        else:
            return {}
            
    def read_all( self, s, namelist):
        d = {}
        for name in namelist:
            d.update(self.read_reg_dict( s, name))
        return d
        
    def freq_counter(self, s):
        return self.read_all(s,
            ["fcnt25","fcnt125","fcnt156_25","fcnt200","fcnt312_5","fcnt322_25"])
            

def test():            
    sysReg = systemReg()
    s = SerialPort(comport='COM11')
    s.connect()

#    print "read_all: ", sysReg.read_all(s, ["date_code","temperature"])
    print "Date Code: ",sysReg.read_reg_dict( s,"date_code" )
#    print "Temperature: ",sysReg.read_reg_dict( s,"temperature" )
#    print "None: ",sysReg.read_reg_dict( s,"None" )
    

