from gevent import monkey
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap
import json
import cgi
from serialcom import SerialPort
import portstatus
from cfg_data import cfgData

import os

def mkpath( relative_path):
    return (os.path.join(os.path.dirname(__file__),relative_path))

class dummy:
    def read_reg32(self,regval):
        return "%0x" % regval
        
    def read_reg64(self,regval):
        return "%0x" % regval


class Register():
    def __init__(self, reg_list):
        self.reg_dict = {}
        for reg_json in reg_list:
            with open(mkpath(reg_json),'r') as fp:
                _dict = json.loads(fp.read())
            self.reg_dict.update(_dict)
            
            
    def read(self, serial, portname, label):
        data = self.reg_dict[label]
        offset = int(data[0],16)
        baseaddr = self.baseaddr(portname)
        offset*=4
        if data[1] == 32:
            regval = serial.read_reg32(offset+baseaddr)
        elif data[1] == 64:
            regval = serial.read_reg64(offset+baseaddr)
        elif data[1] == 48:
            regval = serial.read_reg48(offset+baseaddr)
        return {label: regval}
        
    def write(self, serial, portname, label, value):
        try:
            newval = int(value,16)
        except:
            print "bad write value: %s" % value
            return self.read(serial, portname, label)
        else:
            data = self.reg_dict[label]
            offset = int(data[0],16)
            offset*=4
            baseaddr = self.baseaddr(portname)
            if data[1] == 32:
                serial.write_reg32(offset+baseaddr, newval)
            else:
                low = newval & 0xffffffff
                hi = newval >> 32 & 0xffffffff
                if data[1] == 48:
                    hi = hi & 0xffffffff
                serial.write_reg32(offset+baseaddr, low)
                serial.write_reg32(offset+baseaddr+4, hi)
               
                
        return self.read(serial, portname, label)

        
    def baseaddr(self,portname):
        paddr = {
            'portA': 0xff220000,
            'portB': 0xff224000,
            'portC': 0xff228000,
            'portD': 0xff22c000,
            'portE': 0xff230000,
            'portACSR': 0xff222000,
            'portBCSR': 0xff226000,
            'portCCSR': 0xff22a000,
            'portDCSR': 0xff22e000,
            'portECSR': 0xff232000,
            'portARE': 0xff221000,
            'portBRE': 0xff225000,
            'portCRE': 0xff229000,
            'portDRE': 0xff22d000,
            'portERE': 0xff231000,
}
        return paddr[portname]
        

    def register_update( self, serial, reg_list, portname ):
        baseaddr = self.baseaddr(portname)
        print( "%s  %08x" % (portname, baseaddr))
        data_dict = {}
        for reg_json in reg_list:
            with open(mkpath(reg_json),'r') as fp:
                reg_dict = json.loads(fp.read())
    #        print reg_dict    
            for reg in reg_dict:
    #            print reg
                data = reg_dict[reg]
                offset = int(data[0],16)
                offset*=4
                if data[1] == 32:
                    regval = serial.read_reg32(offset+baseaddr)
                elif data[1] == 64:
                    regval = serial.read_reg64(offset+baseaddr)
                elif data[1] == 48:
                    regval = serial.read_reg48(offset+baseaddr)
                    
                data_dict.update({reg: regval})
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
    reg = Register(['rxcfgstreg.json','txcfgstreg.json','timestampreg.json','rxtxstat.json','PHYregdef.json'])

    
    @app.route('/hello')
    def hello():
        return 'Hello World'

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
    
    @app.route('/phy_config',methods=['POST','GET'] )
    def phy_config():
        return render_template('phy_config.html', title="PHY Config")
    
    if RUN_SOCKETIO:
        socketio = SocketIO(app)

        @socketio.on('connect', namespace='/dd')
        def ws_conn():
            print "ws_conn"
#            data = json.dumps(reg.register_update(serial,['rxcfgstreg.json','txcfgstreg.json','timestampreg.json','rxtxstat.json'], 'portA'))
#            print data
#            socketio.emit('update_table', data, namespace='/dd')
#            port_obj = ps.ps_json(serial)
#            self.socketio.emit('portstatus', port_obj, namespace='/dd')
    #        genthread.connected = True

        @socketio.on('disconnect', namespace='/dd')
        def ws_disconn():
            print "ws_disconn"
        #    thread_stop_event.set()
        #    socketio.emit('portstatus', {'count': c}, namespace='/dd')

        @socketio.on('port_select', namespace='/dd')
        def port_select(message):
            global currentPort
            print(message)
            currentPort = message[1]
            conn(message)

        @socketio.on('panic', namespace='/dd')
        def ws_city(message):
            print(message['panic'])

        @socketio.on('conn', namespace='/dd')
        def conn(message):
            global currentPort
            print "conn message ",message
            socketio.emit('set_portname', currentPort, namespace='/dd')
            if message[0] == 'phy_config':
                data = json.dumps(reg.register_update(serial,['PHYregdef.json'], currentPort+'CSR'))
            elif message[0] == 'mac_config':
                data = json.dumps(reg.register_update(serial,['rxcfgstreg.json','txcfgstreg.json','timestampreg.json'], currentPort))
            elif message[0] == 'mac_statistics':
                data = json.dumps(reg.register_update(serial,['rxtxstat.json'], currentPort))
            socketio.emit('update_table', data, namespace='/dd')
            

        @socketio.on('memwrt', namespace='/dd')
        def memwrt(message):
            global currentPort
            print('memwrt')
            print(message[0])
            print(message[1])
            if message[2] == 'phy_config':
                port_extention = 'CSR'
            else:
                port_extention = ''
            rsp = reg.write(serial, currentPort+port_extention, message[0],message[1])
            print rsp
            data = json.dumps(rsp)
            print data
            socketio.emit('update_table', data, namespace='/dd')

        @socketio.on('getval', namespace='/dd')
        def getval(message):
            print('getval')
            print message
            socketio.emit('update_table',[ message , "and even more!"],namespace='/dd')

        @socketio.on('get_portstatus', namespace='/dd')
        def get_portstatus(message):
            port_obj = ps.ps_json(serial)
            socketio.emit('portstatus', port_obj, namespace='/dd')
            
        print "run socketio"
        socketio.run(app, port=int(cfg["port"]) )
        print "socketio running"
    else:
        app.run( )

import sys
        
def app():
    create_app()
        
app()

