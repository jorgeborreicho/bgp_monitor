'''
    Simple BGP Monitoring tool with JSON API

*****************************************************************************************
Copyright (c) 2018 Jorge Borreicho
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*****************************************************************************************
'''
 
import socket
import sys
import time
from datetime import datetime
import struct
import threading
import http.server
import socketserver
import json


def KeepAliveThread(conn, interval):
     
    #infinite loop so that function do not terminate and thread do not end unless a kill signal is true.
    while not kill_signal:
        time.sleep(interval)
        KeepAliveBGP(conn)

def ReceiveThread(conn):
     
    #infinite loop so that function do not terminate and thread do not end unless a kill signal is true.
    while not kill_signal:
        
        #Receiving from client
        r = conn.recv(1500)
        while True:
            start_ptr = r.find(b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff') + 16
            end_ptr = r[16:].find(b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff') + 16
            if start_ptr >= end_ptr:#a single message was sent in the BGP packet OR it is the last message of the BGP packet
                DecodeBGP(r[start_ptr:])
                break        
            else:#more messages left to decode
                DecodeBGP(r[start_ptr:end_ptr])
                r = r[end_ptr:]
            
def DecodeBGP(msg):
    
    msg_length, msg_type = struct.unpack('!HB',msg[0:3])
    if msg_type == 4:
        #print(timestamp + " - " + "Received KEEPALIVE") #uncomment to debug
        pass
    elif msg_type == 2:
        timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print(timestamp + " - " + "Received UPDATE")

        withdrawn_routes_length = struct.unpack('!H',msg[3:5])[0]
        withdrawn_routes = msg[5:5+ withdrawn_routes_length]
        total_path_attributes_length = struct.unpack('!H',msg[5 + withdrawn_routes_length: 7 + withdrawn_routes_length])[0]
        path_attributes = msg[3 + 2 + withdrawn_routes_length + 2 : 3 + 2 + withdrawn_routes_length + 2 + total_path_attributes_length]
        nlri = msg[3 + 2 + withdrawn_routes_length + 2 + total_path_attributes_length:]
        
        attr = DecodePathAttribute(path_attributes)

        for r in DecodeIPv4Prefix(withdrawn_routes):
            del(rib[r])
        for r in DecodeIPv4Prefix(nlri):
            rib[r] = attr
        
        #uncomment to debug
        #print()
        #print(rib)
        #print()
        
    elif msg_type == 1:
        version, remote_as, holdtime, i1, i2, i3, i4, opt_length = struct.unpack('!BHHBBBBB',msg[3:13])
        timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print(timestamp + " - " + "Received OPEN")
        print()
        print("--> Version:" + str(version) + ", Remote AS: " + str(remote_as) + ", Hold Time:" + str(holdtime) + ", Remote ID: " + str(i1) + "." + str(i2) + "." + str(i3) + "." + str(i4))
        print()
    elif msg_type == 3:
        timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print(timestamp + " - " + "Received NOTIFICATION")
            

def OpenBGP(conn):
    
    #Build the BGP Message
    bgp_version = b'\x04'
    bgp_as = struct.pack('!H',65001)
    bgp_hold_time = struct.pack('!H',30)
    bgp_identifier = struct.pack('!BBBB',10,10,1,1) 

    bgp_opt_lenght = struct.pack('!B',0)
    
    bgp_message = bgp_version + bgp_as + bgp_hold_time + bgp_identifier + bgp_opt_lenght
    
    #Build the BGP Header
    total_length = len(bgp_message) + 16 + 2 + 1;
    bgp_marker = b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    bgp_length = struct.pack('!H', total_length)
    bgp_type = b'\x01'
    bgp_header = bgp_marker + bgp_length + bgp_type
    
    bgp_packet = bgp_header + bgp_message
    
    
    conn.send(bgp_packet)
    return 0
    
def KeepAliveBGP(conn):
    
    #Build the BGP Header
    total_length = 16 + 2 + 1;
    bgp_marker = b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    bgp_length = struct.pack('!H', total_length)
    bgp_type = b'\x04'
    bgp_header = bgp_marker + bgp_length + bgp_type
    
    bgp_packet = bgp_header
    
    
    conn.send(bgp_packet)
    return 0
    
def DecodeIPv4Prefix(bytes):
    ptr = 0
    prefixes = []
    while ptr < len(bytes):
        o1 = 0
        o2 = 0
        o3 = 0 
        o4 = 0
        netmask = struct.unpack('!B',bytes[ptr:ptr+1])[0]
        if netmask <= 8:
            o1 = struct.unpack('!B',bytes[ptr+1:ptr+2])[0]
            ptr = ptr + 2
        elif netmask <= 16:
            o1, o2 = struct.unpack('!BB',bytes[ptr+1:ptr+3])
            ptr = ptr + 3
        elif netmask <= 24:
            o1, o2, o3 = struct.unpack('!BBB',bytes[ptr+1:ptr+4])
            ptr = ptr + 4
        else:
            o1, o2, o3, o4 = struct.unpack('!BBBB',bytes[ptr+1:ptr+5])
            ptr = ptr + 5             
            
        prefixes.append(str(o1) + "." + str(o2) + "." + str(o3) + "." + str(o4) + "/" + str(netmask))
    return prefixes

def DecodePathAttribute(bytes):
    ptr = 0
    path_attributes = dict()
    
    while ptr < len(bytes):
        attribute_flag, attribute_type_code, attribute_length = struct.unpack('!BBB',bytes[ptr:ptr+3])
        if attribute_type_code == 1: #origin
            attribute_value = struct.unpack('!B',bytes[ptr+3:ptr+4])[0]
            if attribute_value == 0:
                path_attributes["origin"] = "IGP"
            elif attribute_value == 1:
                path_attributes["origin"] = "EGP"
            else:
                path_attributes["origin"] = "INCOMPLETE"
        elif attribute_type_code == 2: #as-path  
            as_path = ""
            as_path_type, as_path_length = struct.unpack('!BB',bytes[ptr+3:ptr+5])
            for i in range(as_path_length):
                as_path += str(struct.unpack('!H',bytes[ptr+5+2*i:ptr+7+2*i])[0]) + " "
            path_attributes["as-path"] = as_path.strip() #remove last trailing space    
        elif attribute_type_code == 3: #next-hop
            o1, o2, o3, o4 = struct.unpack('!BBBB',bytes[ptr+3:ptr+7])
            path_attributes["next-hop"] =  str(o1) + "." + str(o2) + "." + str(o3) + "." + str(o4)
        elif attribute_type_code == 4: #med
            path_attributes["med"] = struct.unpack('!I', bytes[ptr+3:ptr+7])[0]
        elif attribute_type_code == 5: #local_pref
            path_attributes["local_pref"] = struct.unpack('!I', bytes[ptr+3:ptr+7])[0]
        elif attribute_type_code == 8: #communities
            communities = ""
            for i in range(attribute_length//4):
                aa = str(struct.unpack('!H',bytes[ptr+3+4*i:ptr+5+4*i])[0])
                nn = str(struct.unpack('!H',bytes[ptr+5+4*i:ptr+7+4*i])[0])
                communities += aa + ":" + nn + " "
            path_attributes["communities"] = communities.strip() #remove last trailing space
            
        ptr = ptr + 3 + attribute_length 
       
    return path_attributes 


class APIHandler(http.server.BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-'):
        timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print(timestamp + " - " + "API Request: ", self.requestline, str(code), str(size))
    
    def log_error(self, format, *args):
        pass
        
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
    def do_GET(self):
        if self.path == "/rib":
            message = str(json.dumps(rib, sort_keys=True, indent=4)) + "\n"
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(message.encode('utf-8'))
        elif self.path == "/count":
            message = str(len(rib)) + "\n"
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(message.encode('utf-8'))
        elif self.path.startswith("/prefix/"):
            prefix = self.path.split("/prefix/")
            try:
                message = str(json.dumps(rib[prefix[1]], sort_keys=True, indent=4)) + "\n"
            except KeyError:
                message = "{}\n"
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(message.encode('utf-8'))
        else:
            self.send_response(404)#bad request
            self.end_headers()
        return
        
class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""   
    
if __name__ == '__main__':
    
    BGP_PEER = '10.10.1.2' #Set your BGP peer IP address here    
    BGP_PORT = 179 # BGP port (179 is the default port for BGP)
    API_PORT = 8000 # Set the JSON API listening port here
    
    kill_signal = False

    rib = dict()
    timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print(timestamp + " - " + "Starting BGP... (peer: " + str(BGP_PEER) + ")")
    
    try:
        bgp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        bgp_socket.connect((BGP_PEER, BGP_PORT))   
        OpenBGP(bgp_socket)
        
    except TimeoutError:
        timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print(timestamp + " - " + "Error: Cannot connect to peer.")
        exit()
        
        
    receive_worker = threading.Thread(target=ReceiveThread, args=(bgp_socket,))#wait from BGP msg from peer and process them
    receive_worker.setDaemon(True)
    receive_worker.start()
    
    keep_alive_worker = threading.Thread(target=KeepAliveThread, args=(bgp_socket,10,))#send keep alives every 10s
    keep_alive_worker.setDaemon(True)
    keep_alive_worker.start()
    
    timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print(timestamp + " - " + "BGP is up.")
    
    try:
        api_server = ThreadedHTTPServer(('', API_PORT), APIHandler)
        timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print(timestamp + " - " + "Starting API server... (port: " + str(API_PORT) + ")")
        print(timestamp + " - " + "Use <Ctrl-C> to stop.")
        api_server.serve_forever()
        
    except KeyboardInterrupt:
        timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print(timestamp + " - " + "^C received, shutting down.")
        kill_signal = True
        try:
            api_server.socket.close()
            bgp_socket.close()
        except:
            pass
        exit()
        
        
    
    