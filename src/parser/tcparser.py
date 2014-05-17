from configparser import SafeConfigParser

class TestcaseParser(object):
    def __init__(self, tcfile):
        # table configuration
        self.sblind = None
        self.bblind = None
        self.bbet = None
        self.ante = None
        self.gtype = None
        self.network = None
        self.tournament = None
        self.balances = []
        
        self.heroHand = None
        self.flopCards = []
        self.turnCard = None
        self.riverCard = None

        self.pfActions = []
        self.flopActions = []
        self.turnActions = []
        self.riverActions = []
        
        self.tcfile = tcfile;


    def _parseActions(self, configText):
        actions = []
        for act in configText.split(','):
            act = act.strip()
            act = act.split(' ')
            actions.append([a.strip() for a in act])
        return actions

    def parse(self):
        
        try:     
            self.config = SafeConfigParser()
            self.config.read(self.tcfile)
    
            config = self.config # shortcut
            
            #preflop section
            self.pfActions = self._parseActions(config.get('preflop', 'actions'))
            self.heroHand = [c.strip() for c in config.get('preflop', 'hand').split(',')]
    
            #flop section
            if(config.has_section('flop')):
                self.flopActions = self._parseActions(config.get('flop', 'actions'))
                self.flopCars = [c.strip() for c in config.get('flop', 'cards').split(',')]
    
            #turn section
            if(config.has_section('turn')):
                self.turnActions = self._parseActions(config.get('turn', 'actions'))
                self.turnCard = config.get('turn', 'card')
    
            #river section
            if(config.has_section('river')):
                self.riverActions = self._parseActions(config.get('river', 'actions'))
                self.riverCard = config.get('river', 'card')
             
            #table config section     
            if(config.has_section('table')):
                if(config.has_option('sblind')):
                    self.sblind = config.getfloat('table', 'sblind')
                if(config.has_option('bblind')):
                    self.bblind = config.getfloat('table', 'bblind')
                if(config.has_option('bbet')):
                    self.bbet = float(config.getfloat('table', 'bbet'))
                if(config.has_option('ante')):
                    self.ante = float(config.getfloat('table', 'ante'))
                if(config.has_option('gtype')):
                    self.gtype = config.get('table', 'gtype')
                if(config.has_option('network')):
                    self.network = config.get('table', 'network')
                if(config.has_option('tournament')):
                    self.tournament = config.getboolean('table', 'tournament')
                if(config.has_option('balances')):
                    balances = config.get('table', 'balances')
                self.balances = [b.split() for b in balances.split(',')]

        except Exception as e:
            raise ParserException(e)
            
            
class ParserException(Exception):
    pass
         

