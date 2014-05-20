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
        """ Parse action line in single actions and check if all actions are valid"""
        
        actions = []
        for action in self._nextActionToken(actionLine):
            # remove parenthesis and whitespaces
            action = action.replace(")","").replace("(","").strip()
            
            # split by whitespace and remove empty whitespace parts
            actionParts = a for action.split(' ') if a 
            if(not self._validAction(actionParts)):
                raise ParserException("Invalid action: " + action)
            
            actions.append(actionParts)
        return actions
    
    def _nextActionToken(self, actionLine):
        """ Return next action token seperated by comma """
        
        iterObj = iter(actionLine.split(','))
        # iterate manually over tokens in order to merge splited tokens in parenthesis again
        while iterObj:
            try:
                token = iterObj.__next__()
                if not "(" in token:
                    yield token
                # if left parenthesis found -> add tokens until right parenthesis found
                else:
                    while not ")" in token:
                        token += iterObj.__next__()
                    yield token
                    
            except StopIteration:
                break
                
    
    def _validAction(self, actionParts):
        """Checks if all parts of an action are valid"""
        
        if(len(actionParts) >= 2):
            # name
            if not re.match(r"[_a-zA-Z]{1}[\S]*", actionParts[0])
                return false
            
            # opponent action
            if len(actionParts) == 2:   
                return re.match(r"([FKCASB]{1})|(R( [0-9]+)?)",actionParts[1])
            # hero action
            else if len(actionParts) >= 4:
                
                if(actionParts[1] == "can" and actionParts[3] = "do" and re.match(r"[FKCRA]+",actionParts[2])
                    for a in actionParts(4:)
                        if not re.match(r"([FKCA]{1})|(R( [0-9]+)?)":
                            return false
                    return true
        return false

    def _validCard(self, card):
        """ Checks if the card is a valid poker card """
        return re.match(r"^[2-9TJQKA]{1}[hsdc]{1}$",card)

    def parse(self):
        """ Start parsing the config file"""
        
        try:     
            config = SafeConfigParser()
            if(not os.path.isfile(self.tcfile)):
                raise ParserException("Invalid file")
            
            config.read(self.tcfile)

            self._parsePreflop(config)
            self._parsePostflop(config)
                          
            self._parseConfig(config)
             
        # map all exceptions to parser exception
        except Exception as e:
            raise ParserException(e)
        
    def _parsePreflop(self,config):
        """Parse the preflop section"""
        
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
        """Parse all postflop sections"""
        
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
         

