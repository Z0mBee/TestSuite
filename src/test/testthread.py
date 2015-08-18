import socket
from PyQt4.QtCore import QThread, SIGNAL, Qt, QWaitCondition, QMutex
from test.autoplayer import AutoPlayer
from testsuite_utility import  LogStyle
from src.parsers.tcparser import TestCaseParser, ParserException
from src.test.testcase import TestCaseStatus

class TestThread(QThread):
    
    def __init__(self, suite, items, stopOnError, stopOnFail):
        QThread.__init__(self)
        self.suite = suite
        self.items = items
        executionDelay = self.suite.sliderSpeed.value() / 1000 # convert to seconds
        self.sync = QMutex()
        self.pauseCond = QWaitCondition()
        self.executionPaused = False  
        self.autoPlayer = AutoPlayer(executionDelay, self.sync, self.pauseCond)
        self.executionStopped = False         
        self.stopOnError = stopOnError
        self.stopOnFail = stopOnFail
        self._connectSignals()
               
    def _connectSignals(self):
        self.connect(self.suite,SIGNAL("pauseExecution"), self.pauseExecution)
        self.connect(self.suite,SIGNAL("unpauseExecution"), self.unpauseExecution)
        self.connect(self.suite,SIGNAL("executionStopped"), self.stopExecution)
        self.connect(self.autoPlayer,SIGNAL("logMessage"), self.suite.logMessage)
        self.connect(self.suite.sliderSpeed, SIGNAL('sliderReleased()'), self.updateExecutionSpeed)
        
    def checkForPause(self):
        """ Check if the pause flag has been set"""
        self.sync.lock()
        if(self.executionPaused):
            self.pauseCond.wait(self.sync)
        self.sync.unlock()

    def run(self):
        self.emit(SIGNAL('updateExecutionButtons'), False)
        # set default icon for all items
        for item in self.items:
            self.emit(SIGNAL('updateItemStatus'), item, TestCaseStatus.UNTESTED, False)
        
        # parse and execute test caeses 
        handNumber = 1  
        failedTc = 0
        successfulTc = 0
        errorTc = 0 
        for item in self.items:     
            try:
                
                self.checkForPause()    
                if self.executionStopped:
                    return
                
                self.emit(SIGNAL('logMessage'), " => Test case : " + item.text(),LogStyle.TITLE)
                self.emit(SIGNAL('updateItemStatus'), item, TestCaseStatus.UNTESTED, True)
                tc = item.data(Qt.UserRole) # get file name
                
                #parse test case 
                tcp = TestCaseParser(tc.file)
                tcp.parse()
                
                #start test
                successful = self.autoPlayer.startTest(tcp, handNumber)
                
                self.checkForPause()
                if self.executionStopped:
                    return
                
                if successful:
                    self.emit(SIGNAL('updateItemStatus'), item, TestCaseStatus.SUCCESS, True)
                    successfulTc += 1
                else:
                    self.emit(SIGNAL('updateItemStatus'), item, TestCaseStatus.FAILED, True)
                    failedTc += 1
                    if(self.stopOnFail):
                        break
                handNumber += 1
            except ParserException as e:
                self.emit(SIGNAL('updateItemStatus'), item, TestCaseStatus.ERROR, True)
                self.emit(SIGNAL('logMessage'),"Parsing error: " + str(e),LogStyle.WARNING)
                errorTc += 1
                if(self.stopOnError):
                    break
            except socket.error:
                self.emit(SIGNAL('logMessage'),"Can't connect to Manual Mode",LogStyle.ERROR)
                self.stopExecution()
                self.emit(SIGNAL('updateExecutionButtons'), True) 
                return
            except Exception as e:
                self.emit(SIGNAL('logMessage'),"Unknown error: " + str(e),LogStyle.ERROR)
                raise         
                '''errorTc += 1
                self.emit(SIGNAL('updateItemStatus'), item, TestCaseStatus.ERROR)
                self.emit(SIGNAL('displayItemDetails'), item)
                if(self.stopOnError):
                  break'''
        
        self.emit(SIGNAL('logMessage'), " => Execution finished",LogStyle.TITLE)
        if(len(self.items) > 1):                 
            self.emit(SIGNAL('logMessage'), "Result => Total: {0}, Successful: {1}, Failed: {2}, Error: {3}"
                      .format(len(self.items),successfulTc,failedTc,errorTc),LogStyle.TITLE)
                
        self.emit(SIGNAL('updateExecutionButtons'), True) 
        
    def pauseExecution(self):
        """ Pause test case execution """
        self.sync.lock()
        self.executionPaused = True
        self.autoPlayer.pause()
        self.sync.unlock()
      
    def unpauseExecution(self):
        """ Unpause test case execution """
        self.sync.lock()
        self.executionPaused = False
        self.autoPlayer.unpause()
        self.pauseCond.wakeAll()
        self.sync.unlock()
        
    def stopExecution(self):   
        """ Stop test case execution """ 
        if(self.executionPaused):
            self.unpauseExecution()
        self.executionStopped = True
        self.autoPlayer.stop()
        
    def updateExecutionSpeed(self):
        executionDelay = self.suite.sliderSpeed.value() / 1000 # convert to seconds
        self.autoPlayer.executionDelay = executionDelay