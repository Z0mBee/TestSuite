import sys
import os
from ui_testsuite import Ui_TestSuite
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from parsers.tcparser import TestCaseParser, ParserException
from autoplayer import AutoPlayer

class LogStyle():
    NORMAL = 1
    TITLE = 2
    SUCCESS = 3
    ERROR = 4
    
class ItemIcon():
    DEFAULT = 1
    ERROR = 2
    FAILED = 3
    SUCCESS = 4
     
class TestsuiteWindow(QMainWindow, Ui_TestSuite):

    def __init__(self, parent=None):
        super(TestsuiteWindow, self).__init__(parent)
        self.setupUi(self)
             
        self.connect(self.buttonAdd,SIGNAL("clicked()"), self.addTestCases)
        self.connect(self.buttonExecute,SIGNAL("clicked()"), self.startExecutingTestCases)
        self.connect(self.buttonExecuteAll,SIGNAL("clicked()"), self.startExecutingAllTestCases)
        
        self._loadIcons()
        self.autoPlayer = AutoPlayer(self)
        self.connect(self.autoPlayer,SIGNAL("logMessage"), self.logMessage)
        self.connect(self.autoPlayer,SIGNAL("setItemIcon"), self.setItemIcon)
        
        
    def _loadIcons(self):
        self.iconSuccess = QIcon("images/circle_green") 
        self.iconError = QIcon("images/circle_error")
        self.iconFailed = QIcon("images/circle_red")
        self.iconDefault = QIcon("images/circle_grey")   
        
    def addTestCases(self):
        fnames = QFileDialog.getOpenFileNames(self, "Select test cases", ".", "Text files (*.txt)")
        self._addTestCasesToList(fnames)
        
    def _addTestCasesToList(self, fnames):        
        for file in fnames: 
                   
            item = QListWidgetItem(os.path.basename(file))
            item.setData(Qt.UserRole,file)
            try:
                tcParser = TestCaseParser(file)
                tcParser.parse()
                self.setItemIcon(item)
                self.logMessage("Added file {0} to test collection".format(os.path.basename(file)))
            except ParserException as e:
                self.setItemIcon(item, ItemIcon.ERROR)
                self.logMessage("Parsing error in file {0}. {1}".format(os.path.basename(file),str(e)),LogStyle.ERROR)
    
            self.listTestCollection.addItem(item)
            
    def startExecutingTestCases(self):
        self.logMessage("Excecute test cases",LogStyle.TITLE)
        self._executeTestCases(self.listTestCollection.selectedItems())
    
    
    def startExecutingAllTestCases(self):
        self.logMessage("Excecute all test cases",LogStyle.TITLE)
        items = [self.listTestCollection.item(i) for i in range(self.listTestCollection.count())]
        self._executeTestCases(items)
            
    def _executeTestCases(self, items):
        # execution in test thread
        self.testThread = TestThread(self,items)
        self.connect(self.testThread,SIGNAL("logMessage"), self.logMessage)
        self.connect(self.testThread,SIGNAL("setItemIcon"), self.setItemIcon)
        self.testThread.start()              
                
    def logMessage(self, msg, style = LogStyle.NORMAL):      
        if(style == LogStyle.NORMAL):
            self.textBrowserLog.append(msg)
        elif(style == LogStyle.TITLE):
            self.textBrowserLog.append('<b>{0}</b>'.format(msg))
        elif(style == LogStyle.ERROR):
            self.textBrowserLog.append('<font color="#FF0000">{0}</font><font color="#000000"></font>'.format(msg))
        elif(style == LogStyle.SUCCESS):
            self.textBrowserLog.append('<font color="#009900">{0}</font><font color="#000000"></font>'.format(msg))
            
    def setItemIcon(self, item, icon = ItemIcon.DEFAULT):
        if(icon == ItemIcon.DEFAULT):
            item.setIcon(self.iconDefault)
        elif(icon == ItemIcon.ERROR):
            item.setIcon(self.iconError)
        elif(icon == ItemIcon.FAILED):
            item.setIcon(self.iconFailed)
        elif(icon == ItemIcon.SUCCESS):
            item.setIcon(self.iconSuccess)


class TestThread(QThread):
    def __init__(self, suite, items):
        QThread.__init__(self)
        self.suite = suite
        self.items = items
        
    def __del__(self):
        self.wait()

    def run(self):
        # set default icon for all items
        for item in self.items:
            self.emit(SIGNAL('setItemIcon'), item, ItemIcon.DEFAULT)
        
        # parse and execute test caeses    
        for item in self.items:     
            try:
                self.emit(SIGNAL('logMessage'), "Test case : " + item.text())
                file = item.data(Qt.UserRole)
                tc = TestCaseParser(file)
                tc.parse()
                self.suite.autoPlayer.startTest(tc)
                self.emit(SIGNAL('setItemIcon'), item, ItemIcon.SUCCESS)
            except ParserException as e:
                self.emit(SIGNAL('setItemIcon'), item, ItemIcon.ERROR)
                self.emit(SIGNAL('logMessage'),"Parsing error: " + str(e),LogStyle.ERROR)
            except Exception as e:
                self.emit(SIGNAL('setItemIcon'), item, ItemIcon.ERROR)
                self.emit(SIGNAL('logMessage'),"Unknown error: " + str(e),LogStyle.ERROR)     
        
               
def startGUI():
    app = QApplication(sys.argv)
    tsw = TestsuiteWindow()
    tsw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    startGUI()