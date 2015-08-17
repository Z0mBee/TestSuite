import socket
from PyQt4.QtCore import QThread, SIGNAL, Qt
from test.autoplayer import AutoPlayer
from testsuite_utility import  LogStyle
from parsers.tcparser import TestCaseParser, ParserException
from src.test.testcase import TestCaseStatus

class TestThread(QThread):
    def __init__(self, suite, items, stopOnError, stopOnFail):
        QThread.__init__(self)
        self.suite = suite
        self.items = items
        executionDelay = self.suite.sliderSpeed.value() / 1000 # convert to seconds
        self.autoPlayer = AutoPlayer(executionDelay)
        self.executionStopped = False       
        self.stopOnError = stopOnError
        self.stopOnFail = stopOnFail
        self._connectSignals()
               
    def _connectSignals(self):
        self.connect(self.suite,SIGNAL("executionStopped"), self.stopExecution)
        self.connect(self.autoPlayer,SIGNAL("logMessage"), self.suite.logMessage)
        self.connect(self.suite.sliderSpeed, SIGNAL('sliderReleased()'), self.updateExecutionSpeed)

    def run(self):
        self.emit(SIGNAL('updateExecutionButtons'), False)
        # set default icon for all items
        for item in self.items:
            self.emit(SIGNAL('updateItemStatus'), item, TestCaseStatus.UNTESTED)
        
        # parse and execute test caeses 
        handNumber = 1  
        failedTc = 0
        successfulTc = 0
        errorTc = 0 
        for item in self.items:     
            try:
                
                if self.executionStopped:
                    return
                
                self.emit(SIGNAL('logMessage'), " => Test case : " + item.text(),LogStyle.TITLE)
                self.emit(SIGNAL('displayItemDetails'), item)
                tc = item.data(Qt.UserRole) # get file name
                
                #parse test case 
                tcp = TestCaseParser(tc.file)
                tcp.parse()
                
                #start test
                successful = self.autoPlayer.startTest(tcp, handNumber)
                
                if self.executionStopped:
                    return
                
                if successful:
                    self.emit(SIGNAL('updateItemStatus'), item, TestCaseStatus.SUCCESS)
                    successfulTc += 1
                else:
                    self.emit(SIGNAL('updateItemStatus'), item, TestCaseStatus.FAILED)
                    failedTc += 1
                    if(self.stopOnFail):
                      break
                handNumber += 1
            except ParserException as e:
                self.emit(SIGNAL('updateItemStatus'), item, TestCaseStatus.ERROR)
                self.emit(SIGNAL('displayItemDetails'), item)
                self.emit(SIGNAL('logMessage'),"Parsing error: " + str(e),LogStyle.ERROR)
                errorTc += 1
                if(self.stopOnError):
                  break
            except socket.error:
                self.emit(SIGNAL('logMessage'),"Can't connect to Manual Mode",LogStyle.ERROR)
                self.stopExecution()
                self.emit(SIGNAL('updateExecutionButtons'), True) 
                return
            '''except Exception as e:
                self.emit(SIGNAL('logMessage'),"Unknown error: " + str(e),LogStyle.ERROR)
                errorTc += 1
                self.emit(SIGNAL('updateItemStatus'), item, TestCaseStatus.ERROR)
                self.emit(SIGNAL('displayItemDetails'), item)
                if(self.stopOnError):
                  break'''
        
        self.emit(SIGNAL('logMessage'), " => Execution finished",LogStyle.TITLE)
        if(len(self.items) > 1):                 
            self.emit(SIGNAL('logMessage'), "Result => Total: {0}, Successful: {1}, Failed: {2}, Error: {3}"
                      .format(len(self.items),successfulTc,failedTc,errorTc),LogStyle.TITLE)
                
        self.emit(SIGNAL('updateExecutionButtons'), True) 
        self.emit(SIGNAL('displayItemDetails'), item)
        
    def stopExecution(self):    
        self.executionStopped = True
        self.autoPlayer.stop()
        
    def updateExecutionSpeed(self):
        executionDelay = self.suite.sliderSpeed.value() / 1000 # convert to seconds
        self.autoPlayer.executionDelay = executionDelay