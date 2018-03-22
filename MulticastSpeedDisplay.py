#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 20 11:22:28 2018
Multicast Network Speed Display
@author: Cooper
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation

import time  
import socket  
from six.moves import queue as Queue
from threading import Thread
import select
import os
  
LOCALIP = '192.168.2.2'  
REMOTEGROUP = '224.0.23.14'
REMOTEPORT = 1314  

##ts packet len
PACKET_LEN = 188*8
global queue 

def data_gen(t=0): #设置xy变量
    x = 0              
    y = 1
    while True:
        now,value = queue.get()
        y = value*8//1024
        #x = time.ctime(now)
        x += 1
        queue.task_done()
        yield x,y  
                       
def init():
    ax.set_xlim(0, 100)                     #起始x 1-10
    ax.set_ylim(0, 5000)                    #设置y相当于0%-100%
    del xdata[:]
    del ydata[:]
    line.set_data(xdata, ydata)
    return line,


def run(data):
    # update the data
    x, y = data
    xdata.append(x)
    ydata.append(y)
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    #表格随数据移动
    if x >= xmax:                      
        ax.set_xlim(xmin+10, xmax+10)
        ax.figure.canvas.draw()
    if y >= ymax:
        ax.set_ylim(ymin, y+500)
        ax.figure.canvas.draw()
        
    line.set_data(xdata, ydata)
    #line.set_color('red')

    return line,


class NetworkWorker(Thread):
    
    def __init__(self,local_ip,remote_ip,remote_port,queue):
        Thread.__init__(self)
        self.queue = queue
        self.local_ip = local_ip
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.sock = self.network_init()

    def run(self):
        ts = time.time()  
        total = 0
        inputs = [self.sock, ]
        while 1:  
            r_list, w_list, e_list = select.select(inputs, [], [], 1.00)
            if not r_list:
                ts = time.time()
                self.queue.put((ts,total))
                total = 0
            else:    
                for r in r_list:
                    if r is self.sock:
                        try:  
                            data, addr = self.sock.recvfrom(PACKET_LEN)
                        except socket.error:  
                                print(self.sock.getpeername(),'disconnected')    
                        else:
                            total += len(data) 
                            new_time = time.time()
                            # 1second
                            if(new_time - ts >= 1):
                                self.queue.put((new_time,total))
                                ts = new_time
                                total = 0
                    
    def network_init(self):  
        #create a UDP socket  
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  
        #allow multiple sockets to use the same PORT number  
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)  
        #Bind to the port that we know will receive multicast data  
        sock.bind((self.local_ip,self.remote_port))  
    
        sock.setsockopt(socket.IPPROTO_IP,  
            socket.IP_ADD_MEMBERSHIP,  
            socket.inet_aton(self.remote_ip) + socket.inet_aton(self.local_ip));  
      
        sock.setblocking(False)
        return sock
    

       
if __name__ == "__main__":  
    fig, ax = plt.subplots(figsize=(8,6),dpi=100)
    ax.set_title( 'Multicast Network Speed [{}:{}]'.format(REMOTEGROUP,REMOTEPORT))
    ax.set_xlabel('Time(s)')
    ax.set_ylabel('Speed(kbps)')
    
    line, = ax.plot([], [], lw=2)              #线像素比

    ax.grid()
    xdata, ydata = [], []
    
    queue=Queue.Queue()
    network=NetworkWorker(LOCALIP,REMOTEGROUP,REMOTEPORT,queue) 
    network.daemon = True
    network.start()

    ani = animation.FuncAnimation(fig, run, data_gen, blit=False, interval=1*1000,
    repeat=False, init_func=init)
    plt.show()


