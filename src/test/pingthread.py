import socket
import xmlrpc.client
from PyQt4.QtCore import QThread, SIGNAL

class PingThread(QThread):
    """ Thread to ping Manual mode and test if connection is possible"""
    
    def __init__(self, suite, xmlRPCUrl):
        QThread.__init__(self)
        self.stopThread = False;
        self.mm = xmlrpc.client.ServerProxy(xmlRPCUrl) 
        self.suite = suite
        self._connectSignals()
        
    def _connectSignals(self):
        self.connect(self.suite,SIGNAL("updateXMLRPCUrl"), self.updateXMLRPCUrl)
        
    def updateXMLRPCUrl(self, xmlRPCUrl):    
        self.mm = xmlrpc.client.ServerProxy(xmlRPCUrl) 
               
    def run(self):
        
        while(not self.stopThread):
          
            try:
                
                self.mm.SetButton("Z", False) # No ping method available atm, so value of not available button is set to test connection
                self.emit(SIGNAL('updateConnectionStatus'), True)
            except socket.error:
                self.emit(SIGNAL('updateConnectionStatus'), False)
          
            QThread.msleep(1000)

