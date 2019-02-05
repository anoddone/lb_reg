import serial
import time


class SerialPort():
    def __init__(self, **kwargs):
        self.comport  = kwargs.get('comport', 'COM1')
        self.baudrate = kwargs.get('baudrate', 115200)
        self.write_timeout = kwargs.get('write_timeout', 31)
        self.timeout = kwargs.get('timeout',10)
        self.connect_retry = kwargs.get('connect_retry',3)
        self.s = None
        self.PROMPT = '# '
        return
        
    def connect(self):
        for attempt in range(self.connect_retry):
            try:
                self.s = serial.Serial(port=self.comport, 
                                       baudrate=self.baudrate, 
                                       write_timeout=self.write_timeout,
                                       timeout=.1)
                break
            except Exception as e:
                print(e)
                input("Correct and press return")
        return self.s
        
    #====================================================================
    #           write_wait() write cmd and wait for a response and
    #           strip off command and prompt from response string
    #====================================================================
    def write_wait( self, cmd, timeout = 60 ):
        """ Write command to the radio and wait for a prompt
            strip off the command echo and the cmd prompt
            return only result of the operation
        """
        cmd = cmd.strip('\n')       # remove any newline
        self.s.write( cmd + '\n' )
        result = self.s.read_until(self.PROMPT, 1024).replace('\r\r\n','')
#        print "until ",result
        result = result.replace(cmd , '')
#        print result
        result = result.strip()
#        result = result.replace(self.PROMPT, '')
        result = result.strip()
        return result

    def read_reg32(self, addr):
        cmd = "md %x 1" % addr
#        print cmd
        reg = self.write_wait(cmd).split()[1]
#        print reg
        return reg.strip()
        
    def write_reg32(self, addr, value):
        cmd = "mw %x %x" % (addr,value)
        print(cmd)
        reg = self.write_wait(cmd).split()[1]
        print(reg)
        return reg
        
    def read_reg64(self, addr):
        low = self.read_reg32(addr)
        hi  = self.read_reg32(addr+4)
        return hi+low

    def read_reg48(self,addr):
        low4 = self.read_reg32(addr)
        hi2  = self.read_reg32(addr+4)
        all = (hi2+low4)[4:16]   #str(hi2[12:16])+str(low4)
        print(hi2,low4,all)
        return all
        

class uut():
    ipaddr = None
    comport = None

    t = None
    s = None
    ssh = None
    
    def __init__(self, **kwargs):
        self.ipaddr = kwargs.get('ipaddr', '192.168.1.20')
        self.comport = kwargs.get('comport', 1)
        self.username = kwargs.get('username','ubnt')
        self.password = kwargs.get('password','ubnt')
        self.retry = kwargs.get('retry', 5)
   
#    def telnet( self ):
#        self.t =  af5ghz_telnet( None )
#        self.t.connect( self.ipaddr, user=self.username, passwd=self.password, retry = self.retry)
        # Need to handle error cases
#        return True

#    def ssh_connect(self):
#        self.ssh = ssh_client()
#        self.ssh.connect(self.ipaddr,user=self.username,passwd=self.password, retry=self.retry)    
    
    def serial( self ):
        if self.comport == None:
            print("Serial comport not defined")
            return False
#        self.s = af5ghz_serial( comport=self.comport, username=self.username, password=self.password )
        # Need to handle error case
        return True
        
        
    def close( self ):
        if self.ssh:
            self.ssh.close()
            self.ssh = None
            
        
           
           
# test code
if __name__ == '__main__':
    s = SerialPort(comport='COM11')
    s.connect()
    data = s.read_reg32(0x60000040)
    print(data)
    data = s.read_reg32(0x60000080)
    print(data)













def readReg( s, addr):
    s.write("md %x 1" % addr)
    rstr = s.read_until('#')
    rsp = rstr.split('/n')
    print(rsp[1])
    data = rsp[1].split( " ")
    print(data)
    return int(data[1], 16)
    
#s = serial.Serial(port='COM11', baudrate=115200, write_timeout=1, timeout=.1)

#print "%0x" % readReg( s, 0x60000000)

#s.close()
