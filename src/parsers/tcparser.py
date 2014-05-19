import os
import re
from configparser import SafeConfigParser

class TestcaseParser(object):
    """ Parses testcase from txt config file"""
    
    def __init__(self, tcfile):
        self.sblind = None
        self.bblind = None
        self.bbet = None
        self.ante = None
        self.gtype = None
        self.network = None
        self.tournament = None
        self.balances = []
        self.hero = None
        
        self.heroHand = None
        self.flopCards = []
        self.turnCard = None
        self.riverCard = None

        self.players = []
        self.pfActions = []
        self.flopActions = []
        self.turnActions = []
        self.riverActions = []
        
        self.tcfile = tcfile;


    def _parseActions(self, actionLine):
        actions = []
        for act in self._nextActionToken(actionLine):
            act = act.replace(")","").replace("(","").strip()
            #if(not self._validAction(act)):
            #    raise ParserException("Invalid action: " + act)
            act = act.split(' ')
            actions.append([a for a in act if a])
        return actions
    
    def _nextActionToken(self, actionLine):
        
        iterObj = iter(actionLine.split(','))

        while iterObj:
            try:
                token = iterObj.__next__()
                if not "(" in token:
                    yield token
                else:
                    while not ")" in token:
                        token += iterObj.__next__()
                    
                    yield token
            except StopIteration:
                break
                
    
    def _validAction(self,action):
        return (re.match(r"^[_a-zA-Z]{1}[\S]* (([FKCASB]{1})|(R( [0-9]+)?))$",action)
                or re.match(r"^[_a-zA-Z]{1}[\S]* can [FKCRA]+ do (([FKCASB]{1})|(R( [0-9]+)?))+$",action))
    
    def _validCard(self,card):
        return re.match(r"^[2-9TJQKA]{1}[hsdc]{1}$",card)

    def parse(self):
        
        try:     
            config = SafeConfigParser()
            if(not os.path.isfile(self.tcfile)):
                raise ParserException("Invalid file")
            
            config.read(self.tcfile)

            self._parsePreflop(config)
            self._parsePostflop(config)
                          
            self._parseConfig(config)
             
    
        except Exception as e:
            raise ParserException(e)
        
    def _parsePreflop(self,config):
        #preflop section
        self.pfActions = self._parseActions(config.get('preflop', 'actions'))
        self.heroHand = [c.strip() for c in config.get('preflop', 'hand').split(',')]
        
        if len(self.heroHand) != 2:
                raise ParserException("Invalid number of hero cards")
        for c in self.heroHand:
            if(not self._validCard(c)):
                raise ParserException("Invalid hero card: " + c)
            
        #find players and hero
        for playerAction in self.pfActions:
            if playerAction[0] not in self.players:
                self.players.append(playerAction[0])
            if len(playerAction) > 3:
                self.hero = playerAction[0]
                
        # put hero at pos 0
        for i in range(0, len(self.players) - self.players.index(self.hero)):
            p = self.players.pop()
            self.players.insert(0, p)
                
        
    def _parsePostflop(self,config):
        #flop section
        if(config.has_section('flop')):
            self.flopActions = self._parseActions(config.get('flop', 'actions'))
            self.flopCards = [c.strip() for c in config.get('flop', 'cards').split(',')]
            
            if len(self.flopCards) != 3:
                raise ParserException("Invalid number of flop cards")
            for c in self.flopCards:
                if(not self._validCard(c)):
                    raise ParserException("Invalid flop card: " + c)
            for playerAction in self.flopActions:
                if(playerAction[0] not in self.players):
                    raise ParserException("Unknown player at the flop: " +playerAction[0])
    
        #turn section
        if(config.has_section('turn')):
            self.turnActions = self._parseActions(config.get('turn', 'actions'))
            self.turnCard = config.get('turn', 'card')
            
            if(not self._validCard(self.turnCard)):
                raise ParserException("Invalid turn card: " + self.turnCard)
            for playerAction in self.turnActions:
                if(playerAction[0] not in self.players):
                    raise ParserException("Unknown player at the turn: " +playerAction[0])
    
        #river section
        if(config.has_section('river')):
            self.riverActions = self._parseActions(config.get('river', 'actions'))
            self.riverCard = config.get('river', 'card')
            
            if(not self._validCard(self.riverCard)):
                raise ParserException("Invalid river card: " + self.riverCard)
            for playerAction in self.riverActions:
                if(playerAction[0] not in self.players):
                    raise ParserException("Unknown player at the river: " +playerAction[0])
        
    def _parseConfig(self,config):
        """ Parse the table config section"""   
        
        #table config section is optional
        if(config.has_section('table')):
            if(config.has_option('table','sblind')):
                self.sblind = config.getfloat('table', 'sblind')
            if(config.has_option('table','bblind')):
                self.bblind = config.getfloat('table', 'bblind')
            if(config.has_option('table','bbet')):
                self.bbet = float(config.getfloat('table', 'bbet'))
            if(config.has_option('table','ante')):
                self.ante = float(config.getfloat('table', 'ante'))
            if(config.has_option('table','gtype')):
                self.gtype = config.get('table', 'gtype')
                if not self.gtype in ('NL', 'PL', 'FL'):
                    raise ParserException("Unknown game type: " +self.gtype)
                                
            if(config.has_option('table','network')):
                self.network = config.get('table', 'network')
            if(config.has_option('table','tournament')):
                self.tournament = config.getboolean('table', 'tournament')
            if(config.has_option('table','balances')):
                balances = config.get('table', 'balances')
            self.balances = [b.split() for b in balances.split(',')]
            
            
class ParserException(Exception):
    pass
         

