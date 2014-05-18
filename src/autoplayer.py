import xmlrpc.client

class AutoPlayer(object):
    """
    Connects to manual mode and peforms actions
    """

    def __init__(self):
        self._connect()
        
    def _connect(self):
        self.mm = xmlrpc.client.ServerProxy('http://localhost:9092') 
        
    def startTest(self,tc):
        
        #init table
        self._resetTable()
        self._addPlayers(tc.players)
        self._setHero(tc.players.index(tc.hero), tc.heroHand[0], tc.heroHand[1]) # hero default at pos 0
        
        sb = tc.pfActions[0][0]

        if len(tc.players) > 2:
            # dealer is sitting before SB
            dealer = tc.players[tc.players.index(sb) - 1]
        else:
            # delaer is SB
            dealer = sb
            
        self._setDealer(tc.players.index(dealer))
        
    def _resetTable(self):
        """Reset table """
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
            
    def _configureTable(self, tc):
        """Configure table for this testcase """

        if tc.sblind:
            self.mm.SetSBlind(self.tc.sblind)
        if tc.bblind:
            self.mm.SetBBlind(self.tc.bblind)
        if tc.bbet:
            self.mm.SetBBet(self.tc.bbet)
        if tc.ante:
            self.mm.SetAnte(self.tc.ante)
        if tc.gtype:
            self.mm.SetGType(self.tc.gtype)
        if tc.network:
            self.mm.SetNetwork(self.tc.network)
        if tc.tournament:
            self.mm.SetTournament(self.tc.tournament)
        if tc.balances:
            for player, balance in self.tc.balances:
                self.mm.SetBalance(self.players.index(player), float(balance))
                
        self.mm.Refresh()
        
    def _doAction(self, action):
        """Do single action on the table. """
        
        if len(action) == 2:
            if action[1] == 'S':
                self.mm.PostSB(self.players.index(action[0]))
            elif action[1] == 'B':
                self.mm.PostBB(self.players.index(action[0]))
            elif action[1] == 'C':
                self.mm.DoCall(self.players.index(action[0]))
            elif action[1] == 'R':
                self.mm.DoRaise(self.players.index(action[0]))
            elif action[1] == 'F':
                self.mm.DoFold(self.players.index(action[0]))
            else:
                raise ValueError("Unknown action: " + action[1])
        elif len(action) == 3:
            if action[1] == 'R':
                self.mm.DoRaise(self.players.index(action[0]),float(action[2]))
            return False
        else:
            # it's heroes turn -> show buttons
            for b in action[2]:
                self.mm.SetButton(b, True)
                
    def _addPlayers(self,players):
        """Add players from testcase to the table."""

        for c,p in enumerate(players):
            self.mm.SetActive(c, True)
            self.mm.SetSeated(c, True)
            self.mm.SetCards(c, 'BB', 'BB')
            self.mm.SetName(c, p)
        self.mm.Refresh()
        
    def _setHero(self, pos, card1, card2):
        self.mm.SetCards(pos, card1, card2)

    def _setDealer(self, pos):
        self.mm.SetDealer(pos)
        