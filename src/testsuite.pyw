import sys
import os
import datetime
from ui_testsuite import Ui_TestSuite
from testsuite_utility import LogStyle
from PyQt4.QtGui import QMainWindow, QKeySequence, QShortcut, QIcon, QFileDialog,\
     QApplication, QPixmap
from PyQt4.QtCore import SIGNAL, Qt
from test.testthread import TestThread
from PyQt4.Qt import QSettings
from test.testcase import TestCaseStatus
from parsers.parsethread import ParseThread
from parsers.parserhelper import ParserHelper
from test.pingthread import PingThread

     
class TestsuiteWindow(QMainWindow, Ui_TestSuite):

    def __init__(self, parent=None):
        super(TestsuiteWindow, self).__init__(parent)
        
        self.setupUi(self)  
        self.parserHelper = ParserHelper()       
        self._connectSignals()      
        self._loadIcons()  
        self.testCollectionFile = None   
        self.testThread = None
        self.parseThread = None
        self.executionPaused = False
        self.readSettings()      
        self._startPingThread()
        
    def closeEvent(self, evnt):    
        self.writeSettings();
        
    def dragEnterEvent(self, event):
        """ Drag enter mouse event"""
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """ Drop mouse event. Accept if urls contain test cases or test collection."""
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            
            files = []
            tcFile = None
            for url in event.mimeData().urls():
                file = url.toLocalFile()
                extension = os.path.splitext(file)[1]
                if extension == ".txt":
                    files.append(file)
                elif extension == ".tc":
                    tcFile = file
            if tcFile:
                event.accept()
                if(self.testCollectionFile):
                    self._loadTestCollectionFile(tcFile, True)
                else:
                    self._loadTestCollectionFile(tcFile, False)
            if files:
                event.accept()
                self._addTestCasesToList(files)  
            else:
                event.ignore()       
        else:
            event.ignore()
        
    
    def _connectSignals(self):
        
        #connect buttons
        self.connect(self.buttonExecute,SIGNAL("clicked()"), self.startExecutingTestCases)
        self.connect(self.buttonExecuteAll,SIGNAL("clicked()"), self.startExecutingAllTestCases)
        self.connect(self.buttonExecuteFailed,SIGNAL("clicked()"), self.startExecutingFailedTestCases)
        self.connect(self.buttonExecuteUntested,SIGNAL("clicked()"), self.startExecutingUntestedTestCases)
        self.connect(self.buttonPause,SIGNAL("clicked()"), self.pauseUnpauseExecution)
        self.connect(self.buttonStop,SIGNAL("clicked()"), self.stopExecuting)
        self.connect(self.buttonAdd,SIGNAL("clicked()"), self.addTestCases)
        self.connect(self.buttonEdit,SIGNAL("clicked()"), self.editSelectedItem)
        self.connect(self.buttonRemove,SIGNAL("clicked()"), self.removeTestCases)
        self.connect(self.buttonRemoveAll, SIGNAL("clicked()"), self.removeAllTestCases)
        self.connect(self.buttonClearLog, SIGNAL("clicked()"), self.textBrowserLog.clear)        
                
        #connect actions
        self.connect(self.actionNew,SIGNAL("triggered()"), self.newTestCollection)
        self.connect(self.actionOpen,SIGNAL("triggered()"), self.openTestCollection)
        self.connect(self.actionSave,SIGNAL("triggered()"), self.saveTestCollection)
        self.connect(self.actionSaveAs,SIGNAL("triggered()"), self.saveAsTestCollection)
        self.connect(self.actionExit,SIGNAL("triggered()"), self.close)
        
        #connect list handling
        self.connect(self.listTestCollection,SIGNAL("itemDoubleClicked(QListWidgetItem *)"), self.editTestcase)
        delKey = QShortcut(QKeySequence(Qt.Key_Delete), self.listTestCollection)
        self.connect(delKey, SIGNAL('activated()'), self.removeTestCases)
        self.connect(self.listTestCollection,SIGNAL("itemSelectionChanged ()"), self.listSelectionChanged)
        
        #others
        self.connect(self.parserHelper,SIGNAL("logMessage"), self.logMessage)

    def _loadIcons(self):
        self.iconSuccess = QIcon("images/circle_green") 
        self.iconError = QIcon("images/circle_error")
        self.iconFailed = QIcon("images/circle_red")
        self.iconDefault = QIcon("images/circle_grey")
        
    def addTestCases(self):
        """Add test cases clicked. Open file selection dialog and add selection to list """
        if(self._isExecuting()):
            self.stopExecuting()
        fnames = QFileDialog.getOpenFileNames(self, "Select test cases", self._lastDirectory, "Text files (*.txt)")
        self._addTestCasesToList(fnames)
        
    def _isExecuting(self):
        """ Testsuite is executing test case if stop button is enabled and test collection is not empty"""
        return self.buttonStop.isEnabled() and self.listTestCollection.count() > 0
    
    def pauseUnpauseExecution(self):
        """ Pause/Unpause test case execution"""
        if(self.executionPaused):
            self.buttonPause.setText("Pause")
            self.emit(SIGNAL('unpauseExecution'))
            self.logMessage("=== Executing unpaused ===",LogStyle.TITLE)
            self.executionPaused = False
        else:
            self.buttonPause.setText("Unpause")
            self.emit(SIGNAL('pauseExecution'))
            self.logMessage("=== Executing paused ===",LogStyle.TITLE)
            self.executionPaused = True

    def editTestcase(self, item):
        """Edit test case in default editor """      
        tc = item.data(Qt.UserRole) 
        os.startfile(tc.file, 'open')
        
    def editSelectedItem(self):
        """User wants to edit the selected item"""
        if(self.listTestCollection.count() > 0):
            self.editTestcase(self.listTestCollection.selectedItems()[0])
                  
    def addItemToList(self, item):
        """ Add item to test collection"""    
        tc = item.data(Qt.UserRole)
        self.listTestCollection.addItem(item)
        if(len(self.listTestCollection.selectedItems()) <= 1):
            self.listTestCollection.clearSelection();
            item.setSelected(True)   
        self.labelTestCases.setText(str(self.listTestCollection.count()))
        self._updateLastDirectory(tc.file)    
            
    def sortListAndUpdateButtons(self):
        self.listTestCollection.sortItems()
        self.updateButtonsToListChange()
           
    def _addTestCasesToList(self, fnames): 
        """Add all files to the list and parse them"""   
        
        if(self.parseThread and self.parseThread.isRunning()):
            self.logMessage("Already adding test cases", LogStyle.ERROR)
            return;   
        
        self.parseThread = ParseThread(fnames, self.listTestCollection, self.parserHelper)
        self.connect(self.parseThread,SIGNAL("logMessage"), self.logMessage)
        self.connect(self.parseThread,SIGNAL("addItemToList"), self.addItemToList)  
        self.connect(self.parseThread,SIGNAL("sortListAndUpdateButtons"), self.sortListAndUpdateButtons)   
        self.connect(self.parseThread,SIGNAL("setItemIcon"), self.setItemIcon)     
        self.parseThread.start()
        
    def displayItemDetails(self, item):
        """ Display the item details"""
        tc = item.data(Qt.UserRole)
        if(tc.hand and len(tc.hand) == 2):
            self.labelHand.setText(tc.hand[0] + " " + tc.hand[1])
        self.labelName.setText(tc.fileName)
        self.textInfo.setText(tc.info)
        if(tc.status == TestCaseStatus.ERROR):
            self.labelStatus.setText("Error")
            self.labelStatus.setStyleSheet("QLabel { color : orange; }");
        elif(tc.status == TestCaseStatus.FAILED):
            self.labelStatus.setText("Failed")
            self.labelStatus.setStyleSheet("QLabel { color : red; }");
        elif(tc.status == TestCaseStatus.SUCCESS):
            self.labelStatus.setText("Success")
            self.labelStatus.setStyleSheet("QLabel { color : green; }");
        else:
            self.labelStatus.setText("Untested")
            self.labelStatus.setStyleSheet("QLabel { color : black; }");
      
    def resetItemDetails(self):
        self.labelName.setText("")
        self.labelHand.setText("")
        self.textInfo.setText("")
        self.labelStatus.setText("")
            
    def listSelectionChanged(self):
        """List selection changed -> update buttons based on selection """
        if(len(self.listTestCollection.selectedItems()) > 0):
            if(not self._isExecuting()):
                self.buttonExecute.setEnabled(True)
            self.buttonEdit.setEnabled(True)
            self.buttonRemove.setEnabled(True)
            
            if(len(self.listTestCollection.selectedItems()) == 1):
                item = self.listTestCollection.selectedItems()[0]
                if(not self._isExecuting()):
                    self.parserHelper.parseListItem(item)
                self.setItemIcon(item, item.data(Qt.UserRole).status)
                self.displayItemDetails(item)
        else:
            self.buttonExecute.setEnabled(False)
            self.buttonEdit.setEnabled(False)
            self.buttonRemove.setEnabled(False)
            
            
    def removeAllTestCases(self):
        """ Remove all test cases from list """
        if(self._isExecuting()):
            self.stopExecuting()
          
        self.logMessage("Removed all files")
        self.listTestCollection.clear()
        self.resetItemDetails()
        self.labelTestCases.setText(str(self.listTestCollection.count()))
        self.updateButtonsToListChange()
      
            
    def removeTestCases(self):
        """ Remove selected test cases from the list """
        if(self._isExecuting()):
            self.stopExecuting()
            
        newSelIndex = 0
        if(len(self.listTestCollection.selectedItems()) > 0):
            newSelIndex = self.listTestCollection.indexFromItem(self.listTestCollection.selectedItems()[0]).row() -1
        
        for item in self.listTestCollection.selectedItems():
            self.logMessage("Removed file {0}".format(item.text())) 
            self.listTestCollection.takeItem(self.listTestCollection.row(item))
               
        if self.listTestCollection.count() == 0:
          self.resetItemDetails()       
               
        if self.listTestCollection.count() > 0:
            if(newSelIndex < 0):
                newSelIndex = 0
            self.listTestCollection.item(newSelIndex).setSelected(True)
            
        self.labelTestCases.setText(str(self.listTestCollection.count()))
        self.updateButtonsToListChange() 
            
    def startExecutingTestCases(self):
        """Execute selected test cases """
        self.logMessage("=== Excecute test cases ===",LogStyle.TITLE)
        self._executeTestCases(self.listTestCollection.selectedItems())
      
    def startExecutingAllTestCases(self):
        """Execute all test cases """
        self.logMessage("=== Excecute all test cases ===",LogStyle.TITLE)
        items = [self.listTestCollection.item(i) for i in range(self.listTestCollection.count())]
        self._executeTestCases(items)
        
    def startExecutingFailedTestCases(self):
        """Execute failed test cases """
        self.logMessage("=== Excecute failed test cases ===",LogStyle.TITLE)
        self._executeTestCases(self.getFailedListItems())      
  
    def startExecutingUntestedTestCases(self):
        """Execute failed test cases """
        self.logMessage("=== Excecute untested test cases ===",LogStyle.TITLE)
        self._executeTestCases(self.getUntestedListItems())  
  
  
    def stopExecuting(self): 
        """Stop executing and send signal to test thread"""      
        self.emit(SIGNAL('executionStopped'))
        self.logMessage("=== Executing stopped ===",LogStyle.TITLE)
        self.updateExecutionButtons(True)
        
    def getUntestedListItems(self):
        """ Return list of all untested items in test collection """
        untestedItems = []
        items = [self.listTestCollection.item(i) for i in range(self.listTestCollection.count())]
        for item in items:
            tc = item.data(Qt.UserRole) 
            if(tc.status == TestCaseStatus.UNTESTED):
                untestedItems.append(item)
        return untestedItems
      
    def getFailedListItems(self):
        """ Return list of all failed items in test collection """
        failedItems = []
        items = [self.listTestCollection.item(i) for i in range(self.listTestCollection.count())]
        for item in items:
            tc = item.data(Qt.UserRole) 
            if(tc.status == TestCaseStatus.FAILED):
                failedItems.append(item)
        return failedItems
        
    def updateExecutionButtons(self, value):
        """Update buttons for execution """
            
        if(len(self.getFailedListItems()) > 0):
            self.buttonExecuteFailed.setEnabled(value)
        if(len(self.getUntestedListItems()) > 0):
            self.buttonExecuteUntested.setEnabled(value)
        
        if(len(self.listTestCollection.selectedItems()) > 0):
            self.buttonExecute.setEnabled(value)
        self.buttonExecuteAll.setEnabled(value)
        self.buttonStop.setEnabled(not value)
        self.buttonPause.setEnabled(not value)
              
    def updateButtonsToListChange(self):
        """Update buttons when number of items in list changed"""
            
        if(len(self.getFailedListItems()) > 0):
            self.buttonExecuteFailed.setEnabled(True)
        else:
            self.buttonExecuteFailed.setEnabled(False)
          
        if(len(self.getUntestedListItems()) > 0):
            self.buttonExecuteUntested.setEnabled(True)
        else:
            self.buttonExecuteUntested.setEnabled(False)
        
        if self.listTestCollection.count() == 0:
            self.buttonExecuteAll.setEnabled(False)
            self.buttonStop.setEnabled(False)
            self.buttonRemoveAll.setEnabled(False)
        else:
            self.buttonExecuteAll.setEnabled(True)
            self.buttonRemoveAll.setEnabled(True)         
            
    def _executeTestCases(self, items):
        """Execute test cases in test thread """
        
        if(self.testThread and self.testThread.isRunning()):
            self. logMessage("Test is still running", LogStyle.ERROR)
            return;
        
        self.testThread = TestThread(self,items, self.checkBoxStopOnError.isChecked(), self.checkBoxStopWhenFailed.isChecked())
        self.connect(self.testThread,SIGNAL("logMessage"), self.logMessage)
        self.connect(self.testThread,SIGNAL("updateItemStatus"), self.updateItemStatus)
        self.connect(self.testThread,SIGNAL("updateExecutionButtons"), self.updateExecutionButtons)
                
        self.testThread.start()              
                
    def updateConnectionStatus(self, isConnected):
        if(isConnected):
            pixmap = QPixmap("images/circle_green")
            self.imageConnectionStatus.setPixmap(pixmap)
        else:
            pixmap = QPixmap("images/circle_red")
            self.imageConnectionStatus.setPixmap(pixmap)
                
    def _startPingThread(self):            
        self.pingThread = PingThread()
        self.connect(self.pingThread,SIGNAL("updateConnectionStatus"), self.updateConnectionStatus)             
        self.pingThread.start()                          
                
    def logMessage(self, msg, style = None):      
        
        if(style == LogStyle.TITLE):
            self.textBrowserLog.append('<font color="#000000"><b>{0}</b></font>'.format(msg))
        elif(style == LogStyle.WARNING):
            self.textBrowserLog.append('<font color="#E59400">{0}</font>'.format(msg))
        elif(style == LogStyle.ERROR):
            self.textBrowserLog.append('<font color="#FF0000">{0}</font>'.format(msg))
        elif(style == LogStyle.SUCCESS):
            self.textBrowserLog.append('<font color="#009900">{0}</font>'.format(msg))
        else:
            self.textBrowserLog.append('<font color="#000000">{0}</font>'.format(msg))
        with open("ts.log","a") as file:
            timeStamp =datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
            file.write(timeStamp +msg + "\n")
      
    def updateItemStatus(self, item, status, updateSelection):
        tc = item.data(Qt.UserRole)
        tc.status = status
        if(updateSelection):
            self.listTestCollection.clearSelection()
            item.setSelected(True)
            self.listTestCollection.scrollToItem(item)
        self.setItemIcon(item, status)
            
    def setItemIcon(self, item, status = None):    
        if(status == TestCaseStatus.ERROR):
            item.setIcon(self.iconError)
        elif(status == TestCaseStatus.FAILED):
            item.setIcon(self.iconFailed)
        elif(status == TestCaseStatus.SUCCESS):
            item.setIcon(self.iconSuccess)
        else:
            item.setIcon(self.iconDefault)

        
    def _updateLastDirectory(self, path):
        if(path):
            self._lastDirectory = os.path.dirname(path)
    
    def saveTestCollection(self):       
        if self.testCollectionFile == None:
            outputFile =  QFileDialog.getSaveFileName(self, "Select file", self._lastDirectory, "Test collection file (*.tc)")  
            self._updateLastDirectory(outputFile)      
        else:
            outputFile = self.testCollectionFile
        self._saveTestCollectionToFile(outputFile)      
        
    def _saveTestCollectionToFile(self, outputFile):
        """Save test cases to test collection file"""
        if(outputFile):
            tcContent = ""
            items = [self.listTestCollection.item(i) for i in range(self.listTestCollection.count())]
            for item in items:
                tc = item.data(Qt.UserRole)
                tcContent += tc.file + "\n"
            with open(outputFile,'w') as file:
                file.write(tcContent)
            self.testCollectionFile = outputFile
            self.labelTestCollection.setText(os.path.basename(outputFile))
            self.logMessage("Saved test collection file " + os.path.basename(outputFile))
    
    def saveAsTestCollection(self):       
        outputFile = QFileDialog.getSaveFileName(self, "Select file", self._lastDirectory, "Test collection file (*.tc)")
        self._updateLastDirectory(outputFile)
        self._saveTestCollectionToFile(outputFile) 
        
    def _loadTestCollectionFile(self, inputFile, addToCollection):
        fNames = []
        with open(inputFile) as file:
            for line in file:
                fNames.append(line.replace("\n",""))
        if(not addToCollection):
            self.listTestCollection.clear()
            self.testCollectionFile = inputFile
            self.logMessage("Loaded test collection file " + os.path.basename(inputFile))
        else:
            self.logMessage("Addded test collection file " + os.path.basename(inputFile))
            
        self.labelTestCollection.setText(os.path.basename(inputFile))  
        self._addTestCasesToList(fNames)
        self.updateButtonsToListChange()
    
    def openTestCollection(self):
        """Open test collection file and load testcases"""
        inputFile = QFileDialog.getOpenFileName(self, "Select file", self._lastDirectory, "Test collection file (*.tc)")
        self._updateLastDirectory(inputFile)
        if(inputFile):
            self._loadTestCollectionFile(inputFile, False)
            
               
    def newTestCollection(self):
        self.listTestCollection.clear()
        self.testCollectionFile = None
        self.labelTestCollection.setText("")  
        self.labelTestCases.setText("")
        self.logMessage("Created new test collection file")
        self.updateButtonsToListChange()
        
    def readSettings(self):
        """Read user settings"""
        settings = QSettings()
        settings.beginGroup("MainWindow")
        if settings.value("size"):
            self.resize(settings.value("size"))
        if settings.value("pos"):
            self.move(settings.value("pos"))
        settings.endGroup()  
          
        self._lastDirectory = settings.value("lastDirectory",".")
        self.sliderSpeed.setValue(settings.value("executionSpeed", 200))
        self.checkBoxStopOnError.setChecked(True  if settings.value("stopOnError") == "true" else False) 
        self.checkBoxStopWhenFailed.setChecked(True  if settings.value("stopWhenFailed") == "true" else False) 
      
    def writeSettings(self):
        """Write user settings"""
        settings = QSettings()
        settings.beginGroup("MainWindow")
        settings.setValue("size", self.size())
        settings.setValue("pos", self.pos())
        settings.endGroup()
        settings.setValue("executionSpeed", self.sliderSpeed.value())
        settings.setValue("lastDirectory", self._lastDirectory)
        settings.setValue("stopOnError", self.checkBoxStopOnError.isChecked()) 
        settings.setValue("stopWhenFailed", self.checkBoxStopWhenFailed.isChecked()) 
    
               
def startGUI():
    app = QApplication(sys.argv)
    app.setOrganizationName("ZomBee")
    app.setOrganizationDomain("zom.bee")
    app.setApplicationName("TestSuite")
    tsw = TestsuiteWindow()
    tsw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    startGUI()