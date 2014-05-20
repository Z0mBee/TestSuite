import time
import xmlrpc.client

class AutoPlayer(object):
    """ Connects to manual mode, configures the table and peforms actions."""

    def __init__(self):
        self._connect()
        
    def _connect(self):
        self.mm = xmlrpc.client.ServerProxy('http://localhost:9092') 
        
    def startTest(self,tc):
              
        self._initTable(tc)
        self._performActions(tc)
            
        
    def _performActions(self, tc):
        for action in tc.pfActions:
            self._doAction(action,tc)
            
        if tc.flopCards:
            self.mm.SetFlopCards(tc.flopCards[0], tc.flopCards[1], tc.flopCards[2])
            for action in tc.flopActions:
                self._doAction(action, tc)
                
        if tc.turnCard:
            self.mm.SetTurnCard(tc.turnCard)
            for action in tc.turnActions:
                self._doAction(action, tc)
            
        if tc.riverCard:
            self.mm.SetRiverCard(tc.riverCard)
            for action in tc.riverActions:
                self._doAction(action, tc)
    
    def _initTable(self, tc):
        """ Initialize the table with all start values"""
        
        self.aborted = False
        self._resetTable()
        self._configureTable(tc)
        self._addPlayers(tc.players)
        # set hero
        self.mm.SetCards(tc.players.index(tc.hero), tc.heroHand[0], tc.heroHand[1])
        
        # sb is always player with first pf action
        sb = tc.pfActions[0][0]

        if len(tc.players) > 2:
            # dealer is sitting before SB
            dealer = tc.players[tc.players.index(sb) - 1]
        else:
            # dealer is SB
            dealer = sb
            
        self.mm.SetDealer(tc.players.index(dealer))
        self.mm.Refresh()
        
    def _resetTable(self):
        """Reset all table values"""
        
        for c in range(0, 10):
            self.mm.SetActive(c, False)
            self.mm.SetSeated(c, False)
            self.mm.SetCards(c, 'NN', 'NN')
            self.mm.SetBalance(c, 1000.0)
            self.mm.SetBet(c, 0.0)
            self.mm.SetPot(0.0)
            self.mm.SetFlopCards('NN', 'NN', 'NN')
            self.mm.SetTurnCard('NN')
            self.mm.SetRiverCard('NN')
            self.mm.SetTournament(True)
        for b in 'FCKRA':
            self.mm.SetButton(b, False)
        self.mm.Refresh()
        time.sleep(0.5)
            
    def _configureTable(self, tc):
        """Configure table for this testcase """

        if tc.sblind:
            self.mm.SetSBlind(tc.sblind)
        if tc.bblind:
            self.mm.SetBBlind(tc.bblind)
        if tc.bbet:
            self.mm.SetBBet(tc.bbet)
        if tc.ante:
            self.mm.SetAnte(tc.ante)
        if tc.gtype:
            self.mm.SetGType(tc.gtype)
        if tc.network:
            self.mm.SetNetwork(tc.network)
        if tc.tournament:
            self.mm.SetTournament(tc.tournament)
        if tc.balances:
            for player, balance in tc.balances:
                self.mm.SetBalance(tc.players.index(player), float(balance))
                
        self.mm.Refresh()
        
    def _doAction(self, action, tc):
        """Do single action on the table. """
        if(self.aborted):
            return
        
        time.sleep(0.5)
        if len(action) == 2:
            if action[1] == 'S':
                self.mm.PostSB(tc.players.index(action[0]))
            elif action[1] == 'B':
                self.mm.PostBB(tc.players.index(action[0]))
            elif action[1] == 'C':
                self.mm.DoCall(tc.players.index(action[0]))
            elif action[1] == 'R':
                self.mm.DoRaise(tc.players.index(action[0]))
            elif action[1] == 'F':
                self.mm.DoFold(tc.players.index(action[0]))
            elif action[1] == 'K':
                pass
            else:
                raise ValueError("Unknown action: " + action[1])
        elif len(action) == 3:
            if action[1] == 'R':
                self.mm.DoRaise(tc.players.index(action[0]),float(action[2]))
            else:
                raise ValueError("Unknown action: " + action[1])
        else:
            # it's heroes turn
            #-> show buttons
            for b in action[2]:
                self.mm.SetButton(b, True)
                
            result = self.mm.GetAction() # get performed action from manual mode
            button = result['button']
            betsize = result['betsize']
            print("Button: {0}  betsize: {1}".format(button,betsize))
            self._resetButtons()
            self.handleHeroAction(button,betsize,tc)
        self.mm.Refresh()
            
            
    def handleHeroAction(self, button, betsize,tc):
        """ Perform hero action in manual mode"""

        if button == 'F':
            self.mm.DoFold(tc.players.index(tc.hero))
            # Abort testcase after bot fold
            self.aborted = True
        elif button == 'C':
            self.mm.DoCall(tc.players.index(tc.hero))
        elif button == 'K':
            pass
        elif button == 'R': # min raise
            self.mm.DoRaise(tc.players.index(tc.hero))
        elif button == 'A': # allin or swag
            if betsize:
                self.mm.DoRaise(tc.players.index(tc.hero), float(betsize))
            else:
                self.mm.DoAllin(tc.players.index(tc.hero))
        self.mm.Refresh()

                
    def _addPlayers(self,players):
        """Add players from testcase to the table."""
        for c,p in enumerate(players):
            self.mm.SetActive(c, True)
            self.mm.SetSeated(c, True)
            self.mm.SetCards(c, 'BB', 'BB')
            self.mm.SetName(c, p)
        self.mm.Refresh()
        
    def _resetButtons(self):
        for b in 'FCKRA':
            self.mm.SetButton(b, False)

        
