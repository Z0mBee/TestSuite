import socket
import xmlrpc.client
from PyQt4.QtCore import QThread, SIGNAL

class PingThread(QThread):
    """ Thread to ping Manual mode and test if connection is possible"""
    
    def __init__(self):
        QThread.__init__(self)
        self.mm = xmlrpc.client.ServerProxy('http://localhost:9092') 
               
    def run(self):
        
        while(True):
          
            try:
                
                self.mm.SetButton("Z", False) # No ping method available atm, so value of not available button is set to test connection
                self.emit(SIGNAL('updateConnectionStatus'), True)
            except socket.error:
                self.emit(SIGNAL('updateConnectionStatus'), False)
          
            QThread.msleep(1000)

