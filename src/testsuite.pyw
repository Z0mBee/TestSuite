import sys
import os
from ui_testsuite import Ui_TestSuite
from parsers.tcparser import TestCaseParser, ParserException
from testsuite_utility import ItemIcon, LogStyle
from PyQt4.QtGui import QMainWindow, QKeySequence, QShortcut, QIcon, QFileDialog,\
    QListWidgetItem, QApplication
from PyQt4.QtCore import SIGNAL, Qt
from test.testthread import TestThread

     
class TestsuiteWindow(QMainWindow, Ui_TestSuite):

    def __init__(self, parent=None):
        super(TestsuiteWindow, self).__init__(parent)
        
        self.setupUi(self)         
        self._connectSignals()      
        self._loadIcons()     


    
    def _connectSignals(self):
        self.connect(self.buttonAdd,SIGNAL("clicked()"), self.addTestCases)
        self.connect(self.buttonExecute,SIGNAL("clicked()"), self.startExecutingTestCases)
        self.connect(self.buttonExecuteAll,SIGNAL("clicked()"), self.startExecutingAllTestCases)
        self.connect(self.buttonStop,SIGNAL("clicked()"), self.stopExecuting)
        self.connect(self.listTestCollection,SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.itemDoubleClicked)
        delKey = QShortcut(QKeySequence(Qt.Key_Delete), self.listTestCollection)
        self.connect(delKey, SIGNAL('activated()'), self.removeTestCases)

    def _loadIcons(self):
        self.iconSuccess = QIcon("images/circle_green") 
        self.iconError = QIcon("images/circle_error")
        self.iconFailed = QIcon("images/circle_red")
        self.iconDefault = QIcon("images/circle_grey")
        
    def addTestCases(self):
        if(self._isExecuting()):
            self.stopExecuting()
        fnames = QFileDialog.getOpenFileNames(self, "Select test cases", ".", "Text files (*.txt)")
        self._addTestCasesToList(fnames)
        
    def _isExecuting(self):
        # Testsuite is executing test case if execute button is disabled and test collection is not empty
        return not self.buttonExecute.isEnabled() and self.listTestCollection.count() > 0
    
    
    def itemDoubleClicked(self, item):
        # open in default enditor
        file = item.data(Qt.UserRole) # get file path
        os.startfile(file, 'open')
    
        
    def _addTestCasesToList(self, fnames):        
        for file in fnames: 
                   
            item = QListWidgetItem(os.path.basename(file))
            item.setData(Qt.UserRole,file)
            try:
                tcParser = TestCaseParser(file)
                tcParser.parse()
                self.setItemIcon(item)
                self.logMessage("Added file {0}".format(os.path.basename(file)))
            except ParserException as e:
                self.setItemIcon(item, ItemIcon.ERROR)
                self.logMessage("Parsing error in file {0}. {1}".format(os.path.basename(file),str(e)),LogStyle.ERROR)
    
            self.listTestCollection.addItem(item)
            
        if self.listTestCollection.count() > 0:
            self.updateButtons(True)
            self.listTestCollection.sortItems()
            
    def removeTestCases(self):
        if(self._isExecuting()):
            self.stopExecuting()
        for item in self.listTestCollection.selectedItems():
            self.logMessage("Removed file {0}".format(item.text())) 
            self.listTestCollection.takeItem(self.listTestCollection.row(item))
            
    def startExecutingTestCases(self):
        self.logMessage("=== Excecute test cases ===",LogStyle.TITLE)
        self._executeTestCases(self.listTestCollection.selectedItems())
    
    
    def startExecutingAllTestCases(self):
        self.logMessage("=== Excecute all test cases ===",LogStyle.TITLE)
        items = [self.listTestCollection.item(i) for i in range(self.listTestCollection.count())]
        self._executeTestCases(items)
        
    def stopExecuting(self):       
        self.emit(SIGNAL('executionStopped'))
        self.logMessage("=== Executing stopped ===",LogStyle.TITLE)
        self.updateButtons(True)
        
    def updateButtons(self, value):
        self.buttonExecute.setEnabled(value)
        self.buttonExecuteAll.setEnabled(value)
        self.buttonStop.setEnabled(not value)
            
    def _executeTestCases(self, items):
        # execution in test thread
        self.testThread = TestThread(self,items)
        self.connect(self.testThread,SIGNAL("logMessage"), self.logMessage)
        self.connect(self.testThread,SIGNAL("setItemIcon"), self.setItemIcon)
        self.connect(self.testThread,SIGNAL("updateButtons"), self.updateButtons)
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

               
def startGUI():
    app = QApplication(sys.argv)
    tsw = TestsuiteWindow()
    tsw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    startGUI()