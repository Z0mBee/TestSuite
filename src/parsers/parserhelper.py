from PyQt4.Qt import Qt, SIGNAL, QObject
from parsers.tcparser import TestCaseParser, ParserException
from testsuite_utility import LogStyle
from test.testcase import TestCaseStatus

class ParserHelper(QObject):

    def parseListItem(self, item):
        """ Parses a list item and sets the status"""
        tc = item.data(Qt.UserRole)
        try:
            tcParser = TestCaseParser(tc.file)
            tcParser.parse()
            tc.info = tcParser.info
            tc.hand = tcParser.heroHand
            if(tc.status == TestCaseStatus.UNTESTED or tc.status == TestCaseStatus.ERROR):
                tc.status = TestCaseStatus.UNTESTED
          
        except ParserException as e:
            self.emit(SIGNAL('logMessage'), "Parsing error in file {0}. {1}".format(tc.fileName,str(e)), LogStyle.WARNING) 
            tc.info = str(e)
            tc.status = TestCaseStatus.ERROR