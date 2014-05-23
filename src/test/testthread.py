import socket
from PyQt4.QtCore import QThread, SIGNAL, Qt
from test.autoplayer import AutoPlayer
from testsuite_utility import ItemIcon, LogStyle
from parsers.tcparser import TestCaseParser, ParserException

class TestThread(QThread):
    def __init__(self, suite, items):
        QThread.__init__(self)
        self.suite = suite
        self.items = items
        executionDelay = self.suite.sliderSpeed.value() / 1000 # convert to seconds
        self.autoPlayer = AutoPlayer(executionDelay)
        self.executionStopped = False
        self._connectSignals()
               
    def _connectSignals(self):
        self.connect(self.suite,SIGNAL("executionStopped"), self.executionStoppend)
        self.connect(self.autoPlayer,SIGNAL("logMessage"), self.suite.logMessage)
        self.connect(self.suite.sliderSpeed, SIGNAL('sliderReleased()'), self.updateExecutionSpeed)
             
    def __del__(self):
        self.wait()

    def run(self):
        self.emit(SIGNAL('updateButtons'), False)
        # set default icon for all items
        for item in self.items:
            self.emit(SIGNAL('setItemIcon'), item, ItemIcon.DEFAULT)
        
        # parse and execute test caeses 
        handNumber = 1   
        for item in self.items:     
            try:
                
                if self.executionStopped:
                    return
                
                self.emit(SIGNAL('logMessage'), " => Test case : " + item.text(),LogStyle.TITLE)
                file = item.data(Qt.UserRole) # get file name
                
                #parse test case 
                tc = TestCaseParser(file)
                tc.parse()
                
                #start test
                successful = self.autoPlayer.startTest(tc, handNumber)
                if successful:
                    self.emit(SIGNAL('setItemIcon'), item, ItemIcon.SUCCESS)
                else:
                    self.emit(SIGNAL('setItemIcon'), item, ItemIcon.FAILED)
                handNumber += 1
            except ParserException as e:
                self.emit(SIGNAL('setItemIcon'), item, ItemIcon.ERROR)
                self.emit(SIGNAL('logMessage'),"Parsing error: " + str(e),LogStyle.ERROR)
            except socket.error:
                self.emit(SIGNAL('logMessage'),"Can't connect to Manual Mode",LogStyle.ERROR)
                self.emit(SIGNAL('updateButtons'), True)
                return
            except Exception as e:
                self.emit(SIGNAL('logMessage'),"Unknown error: " + str(e),LogStyle.ERROR)
                
        self.emit(SIGNAL('updateButtons'), True) 
        
    def executionStoppend(self):    
        self.executionStopped = True
        self.autoPlayer.stop()
        
    def updateExecutionSpeed(self):
        executionDelay = self.suite.sliderSpeed.value() / 1000 # convert to seconds
        self.autoPlayer.executionDelay = executionDelay