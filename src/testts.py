from parsers.tcparser import TestcaseParser
from autoplayer import AutoPlayer

tc = TestcaseParser("testcases/testcase1.txt")
tc.parse()


aPlayer = AutoPlayer()
aPlayer.startTest(tc)