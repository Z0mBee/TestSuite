from PyQt4.QtCore import QThread, SIGNAL, Qt
from test.testcase import  TestCase
from PyQt4.Qt import QListWidgetItem
from os.path import os


class ParseThread(QThread):
    """ Thread gets a list of test cases, parses and adds them to the list"""
    
    def __init__(self, files, listTestCollection, parserHelper):
        QThread.__init__(self)
        self.files = files
        self.listTestCollection = listTestCollection
        self.parserHelper = parserHelper
        
        
    def run(self):
        for file in self.files: 
 
            if(self._fnameInCollection(file)):
                self.emit(SIGNAL('logMessage'), "File {0} is already in test collection".format(os.path.basename(file)))
            else:             
                item = QListWidgetItem(os.path.basename(file))
                tc = TestCase(os.path.basename(file),file)
                item.setData(Qt.UserRole, tc)
                self.emit(SIGNAL('addItemToList'), item)
                self.emit(SIGNAL('logMessage'), "Added file {0}".format(os.path.basename(file))) 
                self.parserHelper.parseListItem(item)
                self.emit(SIGNAL('setItemIcon'), item, tc.status)
        self.emit(SIGNAL('sortListAndUpdateButtons'))
                
    def _fnameInCollection(self,fname):
        """ Check if file name is in test collection"""
        items = [self.listTestCollection.item(i) for i in range(self.listTestCollection.count())]
        for item in items:
            if(fname == item.data(Qt.UserRole).file):
                return True
        return False
    
    