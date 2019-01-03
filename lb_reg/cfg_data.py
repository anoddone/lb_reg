import sys
import json


class cfgData:
    def __init__(self, **kwargs):
        # default setting are passed in
        self.argdict = {}
        self.argdict.update(kwargs)
        
    def cmdline_args(self):
        for i in range(len(sys.argv)):
            if i == 0:
                continue;
            arg = sys.argv[i]
            d = sys.argv[i].split('=')
            if len(d) == 2 and len(d[0]) and len(d[1]):
                self.argdict.update( {d[0]:d[1]})
        return self.argdict
    
    def read_json(self,filename):
        json_data = {}
        try:
            with open(filename,'r') as fp:
                json_data = json.load(fp)
            self.argdict.update(json_data)
        except Exception as e:
            print e
            

    def write_json(self,filename):
        json_data = {}
        try:
            with open(filename,'w') as fp:
                fp.write(json.dumps(self.argdict, indent=4))
        except Exception as e:
            print e
 
    def print_cfg(self):
        for key in self.argdict:
            print "%s=%s" % (key,self.argdict[key])
            
            
    def __getitem__(self, name):
        return self.argdict.get(name)
        
    def get(self,name,default=None):
        item = self.__getitem__(name);
        if item:
            return item
        else:
            return default
    

if __name__ == '__main__':
    cfg = cfgData( portaddr="5000", comport='com11', oneorg='one', twoarg='two')
    print cfg.argdict
    cfg.cmdline_args()
    print cfg.argdict
    print cfg['comport']
    print 'get ',cfg.get('comport',"Noway")
    print 'get ',cfg.get('comport1',"Noway")
    print 'get ',cfg.get('comport1')
    cfg.read_json("dummy.json")
    cfg.write_json("dummy.json")
    cfg1 = cfgData()
    cfg1.read_json('dummy.json')
    print cfg1.argdict
    
    
    