class TestCase:
    '''
    Test case representation
    '''

    def __init__(self, fileName, file):
      self.fileName = fileName
      self.file = file
      self.status = TestCaseStatus.UNTESTED
      self.info = None
      self.hand = None
      
      
class TestCaseStatus:
    UNTESTED = 1
    ERROR = 2
    FAILED = 3
    SUCCESS = 4