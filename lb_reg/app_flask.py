#! /usr/bin/python
from gevent import monkey
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap
import json
import cgi
from serialcom import SerialPort
import portstatus
from cfg_data import cfgData
from system_reg import systemReg
from macro import Macro
import os

def mkpath( relative_path):
    return (os.path.join(os.path.dirname(__file__),relative_path))

class dummy:
    def read_reg32(self,regval):
        return "%0x" % regval
        
    def read_reg64(self,regval):
        return "%0x" % regval


class PageData(object):
    ## create a page to label list dictionary from the json label files
    page_data = [
        ['phy_config',['PHYregdef.json']],
        ['mac_config',['rxcfgstreg.json','txcfgstreg.json','timestampreg.json']],
        ['mac_statistics',['rxtxstat.json']],
        ['ethernet_mac_statistics',['table37statisics.json']],
        ['ethernet_mac_config',['table35config.json']]
    ]
    def __init__(self):
        print("PageData created")
        super(PageData, self).__init__()
        self.pagelabels = {}
        for page in self.page_data:
            reg_labels = []
            for reg_json in page[1]:
#                print reg_json
                with open(mkpath(reg_json),'r') as fp:
                    _dict = json.loads(fp.read())
                for label in _dict:
                    reg_labels.append(label)
            self.pagelabels.update({page[0]: reg_labels})

    def get_page_labels(self,pagename):
        label_list = []
        try:
            label_list = self.pagelabels[pagename]
        except:
            print("page name: %d not found" % pagename)
        return label_list
        
            
class RegGroup(object):
    ## create a register group dictionary to label data dicionary
    reg_group_data = [
        ['CSR',['PHYregdef.json']],
        ['SFP',['rxcfgstreg.json','txcfgstreg.json','timestampreg.json','rxtxstat.json']],
        ['1G',['table37statisics.json','table35config.json']],
        ['RE',[]],
    ]
    def __init__(self):
        print("RegGroup created")
        super(RegGroup, self).__init__()
        self.regGroup = {}
        for group in self.reg_group_data:
#            print group
            reg_list = group[1]
            reg_dict = {}
            for reg_json in reg_list:
                reg_dict_size = len(reg_dict)
                with open(mkpath(reg_json),'r') as fp:
                    _dict = json.loads(fp.read())
                _dict_size = len(_dict)
                reg_dict.update(_dict)
                if (reg_dict_size + _dict_size) > len(reg_dict):
                    print("duplicate entries %d + %d = %d  actual %d" % (reg_dict_size, _dict_size, (reg_dict_size+_dict_size), len(reg_dict)))
            self.regGroup.update({group[0]: reg_dict})
    
    def get_reg_data(self, group, label):
        regdict = self.regGroup[group]
        data = regdict[label]
        return data
        
        
class Register(PageData,RegGroup,Macro):
    def __init__(self, **kwargs):
        print("Register created")
        super(Register, self).__init__()
        self.__dict__.update(kwargs)
        
            
    def read(self, portname, label):
        baseaddr, group = self.baseaddr(portname)
        data = self.get_reg_data(group,label)
        offset = int(data[0],16)
        offset*=4
        if data[1] == 32:
            regval = self.serial.read_reg32(offset+baseaddr)
        elif data[1] == 64:
            regval = self.serial.read_reg64(offset+baseaddr)
        elif data[1] == 48:
            regval = self.serial.read_reg48(offset+baseaddr)
        return {label: regval}
        
    def write(self, portname, label, value):
        try:
            newval = int(value,16)
        except:
            print("bad write value: %s" % value)
            return self.read(portname, label)
        else:
            baseaddr, group = self.baseaddr(portname)
            print("write %x to %s" % (newval,label))
#            data = self.reg_dict[label]
            data = self.get_reg_data(group,label)
            offset = int(data[0],16)
            offset*=4
            print(baseaddr,offset,portname)
            if data[1] == 32:
                self.serial.write_reg32(offset+baseaddr, newval)
            else:
                low = newval & 0xffffffff
                hi = newval >> 32 & 0xffffffff
                if data[1] == 48:
                    hi = hi & 0xffffffff
                self.serial.write_reg32(offset+baseaddr, low)
                self.serial.write_reg32(offset+baseaddr+4, hi)
               
        self.write_log(portname,label,value)       
        return self.read( portname, label)

    def baseaddr(self,portname):
        paddr = {
            'portA': [0xff220000,"SFP"],
            'portB': [0xff224000,"SFP"],
            'portC': [0xff228000,"SFP"],
            'portD': [0xff22c000,"SFP"],
            'portE': [0xff230000,"SFP"],
            'portACSR': [0xff222000,"CSR"],
            'portBCSR': [0xff226000,"CSR"],
            'portCCSR': [0xff22a000,"CSR"],
            'portDCSR': [0xff22e000,"CSR"],
            'portECSR': [0xff232000,"CSR"],
            'portARE': [0xff221000,"RE"],
            'portBRE': [0xff225000,"RE"],
            'portCRE': [0xff229000,"RE"],
            'portDRE': [0xff22d000,"RE"],
            'portERE': [0xff231000,"RE"],
            'portA1G': [0xff240000,"1G"],  # port A is missing! using B address
            'portB1G': [0xff240000,"1G"],
            'portC1G': [0xff240400,"1G"],
            'portD1G': [0xff240800,"1G"],
            'portE1G': [0xff240c00,"1G"],
        }
        data = paddr[portname]
        return data[0],data[1]
        
    def mem_write_log(self, portname,regname,value):
        access_list=[]
        filepath = mkpath("config/config.json")
        with open(mkpath(filepath),'r') as fp:
            access_list = json.loads(fp.read())
        access_list.append([regname,value,portname])
        with open(mkpath(filepath),'w') as fp:
            fp.write(json.dumps(access_list,indent=4))

    def page_update( self, pagename, portname ):
        label_list = self.get_page_labels(pagename)
        data_dict = {}
        for label in label_list:
            data = self.read( portname, label)
            data_dict.update(data)
        return data_dict

currentPort = "portA"

RUN_SOCKETIO = True
def create_app():
    global currentPort
    cfg = cfgData(host='127.0.0.1', port='5000', comport='COM11')
    cfg.cmdline_args()      # command line overrides default
    cfg.print_cfg()
    serial = SerialPort(comport=cfg['comport'])
    serial.connect()

    #   monkey.patch_all()
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.debug = False
    app.secret_key = 'development key'
    bootstrap = Bootstrap(app)
    ps = portstatus.PortStatus(0xff200000)
    reg = Register(serial=serial)
    sysReg = systemReg(0xff200000)
    
    @app.route('/bs4')
    def bs4():
        return render_template('bs4.html')

    @app.route('/', methods=['POST','GET'])
    def portstatus_json():
        print( "port_status_json()")
        return render_template('portstatus_json.html')

    @app.route('/status_table')
    def status_table():
        print( "status_table()")
        return render_template('status_table.html')
        
    @app.route('/status', methods=['POST','GET'])
    def status():
        return render_template('status_table.html', title="Table Port Status")
    
    @app.route('/sfpcfg',methods=['POST','GET'] )
    def sfpcfg():
        return render_template('sfpcfg.html', title="SFP Config")
    
    @app.route('/mac_config',methods=['POST','GET'] )
    def mac_config():
        return render_template('mac_config.html', title="MAC Config")
    
    @app.route('/mac_statistics',methods=['POST','GET'] )
    def mac_status():
        return render_template('mac_statistics.html', title="MAC Statistics")
    
    @app.route('/ethernet_mac_statistics',methods=['POST','GET'] )
    def ethernet_mac_statistics():
        return render_template('ethernet_mac_statistics.html', title="ethernet MAC Statistics")
    
    @app.route('/ethernet_mac_config',methods=['POST','GET'] )
    def ethernet_mac_config():
        return render_template('ethernet_mac_config.html', title="ethernet MAC Config")
    
    @app.route('/phy_config',methods=['POST','GET'] )
    def phy_config():
        return render_template('phy_config.html', title="PHY Config")
    
    if RUN_SOCKETIO:
        socketio = SocketIO(app)

        @socketio.on('connect', namespace='/dd')
        def ws_conn():
            print("ws_conn")

        @socketio.on('disconnect', namespace='/dd')
        def ws_disconn():
            print("ws_disconn")
        #    thread_stop_event.set()
        #    socketio.emit('portstatus', {'count': c}, namespace='/dd')

        @socketio.on('macro', namespace='/dd')
        def macro(msg):
            print("macro")
            reg.macro(msg)
            data = reg.macro_status()
            print(data)
            if msg[0] == "play":
                conn([msg[2],currentPort])
            else:
                socketio.emit('macro_status',data, namespace='/dd')

        @socketio.on('port_select', namespace='/dd')
        def port_select(message):
            global currentPort
            print(("port_select ",message, currentPort))
            if (message[0] == 'ethernet_mac_statistics' or message[0] == 'ethernet_mac_config'  ) and message[1] == "portA":
                message[1] = currentPort
            print(message)
            currentPort = message[1]
            conn(message)

        @socketio.on('panic', namespace='/dd')
        def ws_city(message):
            print((message['panic']))

        @socketio.on('conn', namespace='/dd')
        def conn(message):
            global currentPort
            print("conn message ",message)
            socketio.emit('set_portname', currentPort, namespace='/dd')
            if message[0] == 'phy_config':
                data = json.dumps(reg.page_update(message[0], currentPort+'CSR'))
                socketio.emit('update_table', data, namespace='/dd')
            elif message[0] == 'mac_config':
                data = json.dumps(reg.page_update(message[0], currentPort))
                print(data)
                socketio.emit('update_table', data, namespace='/dd')
            elif message[0] == 'mac_statistics':
                data = json.dumps(reg.page_update(message[0], currentPort))
                socketio.emit('update_table', data, namespace='/dd')
            elif message[0] == 'ethernet_mac_statistics':
                if currentPort == "portA":
                    currentPort = "portB"
                data = json.dumps(reg.page_update(message[0], currentPort+'1G'))
                socketio.emit('update_table', data, namespace='/dd')
            elif message[0] == 'ethernet_mac_config':
                if currentPort == "portA":
                    currentPort = "portB"
                data = json.dumps(reg.page_update(message[0], currentPort+'1G'))
                socketio.emit('update_table', data, namespace='/dd')
            data = json.dumps(sysReg.read_all(serial, ["date_code","temperature"]))
            socketio.emit('update_system', data, namespace='/dd')
            data = reg.macro_status()
            print(data)
            socketio.emit('macro_status',data, namespace='/dd')
            

        @socketio.on('memwrt', namespace='/dd')
        def memwrt(message):
            global currentPort
            print('memwrt')
            print((message[0]))
            print((message[1]))
            if message[2] == 'phy_config':
                port_extention = 'CSR'
                rsp = reg.write( currentPort+port_extention, message[0],message[1])
            elif message[2] =='ethernet_mac_config':
                port_extention = '1G'
                rsp = reg.write( currentPort+port_extention, message[0],message[1])
            else:
                port_extention = ''
                rsp = reg.write( currentPort+port_extention, message[0],message[1])
            print(rsp)
            data = json.dumps(rsp)
            print(data)
            socketio.emit('update_table', data, namespace='/dd')
            socketio.emit('macro_status',reg.macro_status(), namespace='/dd')

        @socketio.on('getval', namespace='/dd')
        def getval(message):
            print('getval')
            print(message)
            socketio.emit('update_table',[ message , "and even more!"],namespace='/dd')

        @socketio.on('get_portstatus', namespace='/dd')
        def get_portstatus(message):
            port_obj = ps.ps_json(serial)
            socketio.emit('portstatus', port_obj, namespace='/dd')
            data = json.dumps(sysReg.read_all(serial, ["date_code","temperature"]))
            socketio.emit('update_system', data, namespace='/dd')
            data = json.dumps(sysReg.freq_counter(serial))
            socketio.emit('update_system', data, namespace='/dd')
           
        print("run socketio")
        socketio.run(app, port=int(cfg["port"]) )
        print("socketio running")
    else:
        app.run( )

import sys
        
def app():
    create_app()
        
app()

