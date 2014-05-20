import sys
import os
from ui_testsuite import Ui_TestSuite
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from parsers.tcparser import TestCaseParser, ParserException
 
class TestsuiteWindow(QMainWindow, Ui_TestSuite):

    def __init__(self, parent=None):
        super(TestsuiteWindow, self).__init__(parent)
        self.setupUi(self)
        
        
        self.buttonAdd.clicked.connect(self._addTestCases)
        self.buttonExecute.clicked.connect(self._executeTestcases)
        self.buttonExecuteAll.clicked.connect(self._executeAllTestcases)
        
        self._loadIcons()
        
        
    def _loadIcons(self):
        self.iconSuccess = QIcon("images/circle_green") 
        self.iconError = QIcon("images/circle_error")
        self.iconFailed = QIcon("images/circle_red")
        self.iconDefault = QIcon("images/circle_grey")   
        
    def _addTestCases(self):
        fnames = QFileDialog.getOpenFileNames(self, "Select test cases", ".", "Text files (*.txt)")
        self._addTestCasesToList(fnames)
        
    def _addTestCasesToList(self, fnames):        
        for file in fnames: 
                   
            item = QListWidgetItem(os.path.basename(file))
            item.setData(Qt.UserRole,file)
            try:
                tcParser = TestCaseParser(file)
                tcParser.parse()
                item.setIcon(self.iconError)
            except ParserException as e:
                item.setIcon(self.iconDefault)
                self.textBrowserLog.append(str(e))
    
            self.listTestCollection.addItem(item)
            
    def _executeTestcases(self):
        for item in self.listTestCollection.selectedItems():
            item.setIcon(self.iconSuccess)
    
    
    def _executeAllTestcases(self):
        for i in range(self.listTestCollection.count()):
            self.listTestCollection.item(i).setIcon(self.iconFailed)    
    
def startGUI():
    app = QApplication(sys.argv)
    tsw = TestsuiteWindow()
    tsw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    startGUI()