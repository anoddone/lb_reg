
from bs4 import BeautifulSoup
import urllib2
import sys
import json
print sys.getdefaultencoding()
reload(sys)  
sys.setdefaultencoding('cp1252')
print sys.getdefaultencoding()

form =  '<td>\n' +\
        '<form method="post">\n' +\
            '<input type="text" class="reg_input" id="%s" value="%s" %s></input>\n' +\
        '</form>\n' +\
        '</td>\n'

header_button ='<button type="button"  class="btn btn-default hideclass" ><span class="glyphicon glyphicon-resize-vertical"></span></th>\n'

htmlhdr ='{% extends "base.html" %}\n' + \
        '{% block content %}\n' + \
        '<div class="container">\n'
htmlhdr2=  '<h1>%s</h1>\n' + \
        '</div>\n\n'

# build the html page.
# assembly includes: FLASK header, page name, html tables, and the javascript.html
def build_html( html_filename, table_list, page_name):
    print page_name
    print htmlhdr
    with open( 'templates/%s.html'% html_filename, 'w') as fp:
        print (htmlhdr2 % page_name )
        fp.write(htmlhdr + (htmlhdr2 % page_name))
        for table in table_list:
            with open("templates/%s.html"% table,'r') as fpr:
                content = fpr.read()
                fp.write(content)
        with open("templates/javascript.html",'r') as fpr:
            content = fpr.read()
            fp.write(content)






def makeTable(table_data, table_name=None, table_header=None):
    nrow = len(table_data)
    ncol = len(table_data[0])
    html =""
    if table_name:
        html += '<h1>'+table_name+'</h1>\n'
        html += '<table class="table">\n<tbody>\n'
    if table_header:
        html += '<tr>\n'
        html += '<th class="col0">'+table_header[0]+'</th>\n'
        html += '<th class="col1">'+table_header[1]+'</th>\n'
        html += '<th class="col2">'+table_header[2]+'</th>\n'
        html += '<th class="col3">'+table_header[3]+ header_button + '</th>\n'
        html += '<tr>\n'
    for row in table_data:
        value=label=default=desc=access=''
        if len(row) == 0: continue
        try:
            value = row[0]
            label  = row[1]
            default = row[2]
            desc   = row[3].replace('\n','\n<br>')
            access = row[4].strip()
        except:
            print "row short"
            print row
        if access == 'RO':
            disable = 'disabled '
        else:
            disable = ""
        html += '<tr>\n'
        html +=  (form  % (label,default,disable))
        html += '<td>' + label + '</td\n>'
        html += '<td>' + default + '</td\n>'
        html += '<td >' + desc + '</td\n>'
        html += '</tr>\n'
        
    html += '</tbody></table>'
    return html

def extract_table_data( filename):
    with open("templates/raw/%s.html"% filename,'r') as fp:
        content = fp.read()

    soup = BeautifulSoup(content, features="lxml")

    #print soup.prettify()

    table = soup.table
    #print table
    thead = table.thead
    tbody = table.tbody

    rows =  table.find_all(['tr'])
    #print len(rows)
    #print rows

#    for row in table.find_all(['th','tr']):
#        for cell in row(["th"]):
#            print cell.text
#    print "Done"

    table_data = [[cell.text.decode("utf-8",errors="ignore").replace('\t','').strip() for cell in row("td")]
                             for row in table.find_all("tr")]
    #print table_data

    with open("table_data/%s.json"%filename, 'w') as fp:
        fp.write(json.dumps(table_data, indent=4))
   
def process_table( filename, table_name, default_access="",default_default="",regsize=32, MAC=None):
    extract_table_data(filename)

    with open("templates/raw/%s.html"% filename,'r') as fp:
        content = fp.read()

    soup = BeautifulSoup(content, features="lxml")

    #print soup.prettify()

    table = soup.table
    #print table
    thead = table.thead
    tbody = table.tbody

    rows =  table.find_all('tr')
    #print len(rows)
    #print rows

    #for row in table.find_all('td'):
    #    print row

    table_data = [[cell.text for cell in row("td")]
                             for row in table.find_all("tr")]
    print table_data
    with open("%stable_data.json"%filename, 'w') as fp:
        fp.write(json.dumps(table_data, indent=4))
    table_dict = {}
    table_list = []
    if MAC:
        label ="MAC"
        offset = "0x10"
        value = default = "000000000000"
        desc = "MAC address"
        access = "RW"
        table_dict.update( {label : [offset,48] })
        table_list.append( [value,label,default,desc,access])

    print "len(table_data) ", len(table_data)
    for row in table_data:
        if len(row) == 0:
            continue
        value = "0x12345"
        print row
        offset = row[0].strip().split('\n')[0]
        offset = offset.split(':')[0]
        if offset.count('0x') == 0:
            continue
        label = ""
        try:
            label = row[1].strip().split()[0]
        except:
            print "missing label"
            continue
        if label == 'Reserved':
            continue
        if len(row) > 2:
            desc = (row[2].decode("utf-8",errors="ignore")).replace('\t','').strip()
        else:
            desc = ""
        if len(row) > 3:
            access = (row[3].decode( 'utf-8',errors="ignore")).replace("\t","")
        else:
            access = default_access
        if len(row) > 4:
            default = (row[4].decode( 'utf-8',errors="ignore")).replace("\t","")
        else:
            default = default_default
        table_dict.update( {label : [offset,regsize] })
        table_list.append( [value,label,default,desc,access])
           
    html = makeTable(table_list, 
            table_name=table_name,
            table_header=["Current Value","Register Name","HW Reset Value","Description"])
#    print html
    with open("templates/%s.html"% filename,'w') as fp:
        fp.write(html)

    with open("%s.json"%filename, 'w') as fp:
        fp.write(json.dumps(table_dict, indent=4))
    #    for row in table_data:
    #    print "%20s %s %60s"  % (repr(row[0]), row[1], repr(row[2]))
    #    print "%s\t%s\t\n" %(row[0], row[1][0]),
    #    print row[0].strip(),row[1].strip(),(row[2].encode( 'utf-8')).replace("\t","")

def create_html(filename, table_header, **kwargs):
    with open("table_data/%s.json"% filename,'r') as fp:
        table_data = json.load(fp)
        makeTable(table_data, table_name=None, table_header=table_header)                


def extract_data(table_list):
    for table in table_list:
        extract_table_data(table)

if __name__ == '__main__':
    process_table( 'txcfgstreg', "Table 25.  MAC TX Configuration and Status Register", MAC=True)
    sys.exit()
#    extract_data(['txcfgstreg','rxcfgstreg', 'timestampreg','rxtxstat','PHYregdef'])
    create_html( 'txcfgstreg', "Table 25.  MAC TX Configuration and Status Register")
    create_html( 'rxcfgstreg', "Table 28.  MAC RX Configuration and Status Register")
    create_html( 'timestampreg', "Table 29.  MAC Timestamp Registers")
    create_html( 'rxtxstat', "Table 34.  MAC TX and RX Statistics Registers")
    sys.exit()
    process_table( 'rxcfgstreg', "Table 28.  MAC RX Configuration and Status Register")
    build_html('mac_config', [ 'txcfgstreg','rxcfgstreg', 'timestampreg'], "MAC Configuration and Status")
    build_html('mac_statistics', [ 'rxtxstat'],'MAC Tx and Rx Statistics')
   
    process_table( 'PHYregdef', "Table 159.  PHY Register Definitions")
    build_html('phy_config', [ 'PHYregdef'],'PHY Configuartion and Status')
#    process_table( 'timestampreg', "Table 29.  MAC Timestamp Registers")
#    process_table( 'rxtxstat', "Table 34.  MAC TX and RX Statistics Registers", default_access='RO',default_default='0x0', regsize=64)




