import os
import json
import datetime


class Macro(object):
    def __init__(self, **kwarg):
        super(Macro,self).__init__()
        self.dir_path = os.path.join('.','config')
        self.rec_buffer = []
        self.record = False
        self.entries = 0
        
        
    def macro(self,msg):
        print(msg,msg[0])
        cmd = msg[0]
        if cmd == 'record':
            self.record_btn(msg)
        elif cmd == 'clear':
            self.clear(msg)
        elif cmd == 'play':
            self.play(msg)
        elif cmd == 'save':
            self.save(msg)
        else:
            print("unknown message: ",msg)
    
    def record_btn(self,msg):
        if self.record:
            self.record=False
        else:
            self.record=True
        print(self.record)
            
    def clear(self,msg):
        self.rec_buffer = []
        self.entries = 0
        return
        
    def play(self,msg):
        save_record = self.record
        self.record = False
        filename = os.path.join(self.dir_path,msg[1]+'.json')
        with open(filename,'r') as fp:
            write_list = json.loads(fp.read())
        for reg in write_list:
            self.write(reg[2],reg[0],reg[1])
        self.record = save_record    
        return
        
    def save(self,msg):
        print(msg)
#        if self.entries == 0:
#            return
        filename = self.mk_filename()
        if filename:
            with open(filename,'w') as fp:
                fp.write(json.dumps(self.rec_buffer,indent=4))
        
        self.rec_buffer = []
        self.entries = 0
        self.record = False
        return
        
    def write_log(self, portname, label, value):
        print("write_log()")
        if not self.record:
            return
        self.entries+=1
        self.rec_buffer.append([label,value,portname])
        print(self.entries, self.rec_buffer)
        
    def str_match(self, match, slist):
        print(match,slist)
        itmatched = False
        for s in slist:
            print(s,match)
            if s == match:
                itmatched = True
                
        return itmatched
                
    def mk_filename(self):
        max = 50
        files = self.config_files()
        basename = 'm' + "{:%y%m%d}".format(datetime.datetime.today())
        for i in range(max):
            filename = basename + str(i) + '.json'
            print(files)
            print(filename)
            if self.str_match( filename,files) == False:
#           if [x for x in files if x == filename] == False:
                return os.path.join(self.dir_path,filename)
        print("too many duplicate filenames: ",filename)
        return None
                
         
#           if [x for x in files if x == filename] == False:
#               return filename
        print("too many duplicate filenames: ",filename)
        return ""
            
        
    
    def config_files(self):
        return [f for f in os.listdir(self.dir_path) if f.count('.json')]
    
    def macro_status(self):
        files = []
        for file in self.config_files():
            files.append(file.replace('.json',''))
        
        data = ['Stop' if self.record else 'Start',str(self.entries),files]
        return json.dumps(data)
    
    

        