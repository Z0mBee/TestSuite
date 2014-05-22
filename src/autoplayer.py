import time
import xmlrpc.client
from PyQt4.Qt import QObject, SIGNAL
from testsuite_utility import LogStyle

class AutoPlayer(QObject):
    """ Connects to manual mode, configures the table and peforms actions."""

    def __init__(self, executionDelay):
        QObject.__init__(self)
        self._connect()
        self.executionDelay = executionDelay
        
    def _connect(self):
        self.mm = xmlrpc.client.ServerProxy('http://localhost:9092') 

    def startTest(self,tc):
        
        self.testFailed = False 
        self._initTable(tc)
        self._performActions(tc)
        
        if self.testFailed:
            return False
        else: 
            return True
        
    def stop(self):
        self.aborted = True
        self.testFailed = True
        
    def _performActions(self, tc):
           
        if self.aborted:
                return;
        self.emit(SIGNAL('logMessage'), "--- Preflop --- Cards : {0}, {1}".format(tc.heroHand[0], tc.heroHand[1]))
        for action in tc.pfActions:
            if self.aborted:
                    return;
            self._doAction(action,tc)
                   
        if tc.flopCards:
            self.emit(SIGNAL('logMessage'), "--- Flop --- Cards : {0}, {1}, {2}".format(tc.flopCards[0],tc.flopCards[1],tc.flopCards[2])) 
            self.mm.SetFlopCards(tc.flopCards[0], tc.flopCards[1], tc.flopCards[2])
            for action in tc.flopActions:
                if self.aborted:
                    return;
                self._doAction(action, tc)
                
        if tc.turnCard:
            self.emit(SIGNAL('logMessage'), "--- Turn --- Card : {0}".format(tc.turnCard)) 
            self.mm.SetTurnCard(tc.turnCard)
            for action in tc.turnActions:
                if self.aborted:
                    return;
                self._doAction(action, tc)
            
        if tc.riverCard:
            self.emit(SIGNAL('logMessage'), "--- River --- Card : {0}".format(tc.riverCard)) 
            self.mm.SetRiverCard(tc.riverCard)
            for action in tc.riverActions:
                if self.aborted:
                    return;
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
        
    def _resetTable(self):
        """Reset all table values"""
        
        self.mm.CancelGetAction()
        
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
        
    def _doAction(self, action, tc):
        """Do single action on the table. """
        actionString = ""
        for a in action:
            actionString += a + " "
        
        self.emit(SIGNAL('logMessage'), "Action: " + actionString)
        time.sleep(self.executionDelay)
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
            self._showHeroButtons(action[2], tc)

            try:
                result = self.mm.GetAction() # get performed action from manual mode
            except: # TODO: Problem with stopping executin when waitin for action
                self.aborted = True
                return
            button = result['button']
            betsize = result['betsize']
            self._resetButtons()
            self._performHeroAction(button,betsize,tc)
            self._compareActionWithTestCase(button, betsize, action, tc)
        self.mm.Refresh()
            
    def _showHeroButtons(self, buttons, tc):
        for b in buttons:
            # map button R to button A when game type is NL
            if b == "R" and tc.gtype == "NL":
                self.mm.SetButton("A",True)
            else:
                self.mm.SetButton(b, True)
    
    def _performHeroAction(self, button, betsize,tc):
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
                self.aborted = True # Abort testcase after all-in
        self.mm.Refresh()
        
    def _compareActionWithTestCase(self, button, betsize, heroAction, tc):
        
        expectedActions = heroAction[4:] # all possible hero actions
        eaString = ""
        # raise button in mm is A -> handle like R button has been pressed
        if button == "A" and betsize:
            button = "R"
            
        # build expected action string without digits
        for ea in expectedActions:
            if not ea.isdigit():
                eaString += ea +" "
            
        # find bet size
        expectedBetsize = "Any" #default bet size is any
        for a in expectedActions:
            if a.isdigit():
                expectedBetsize = a

        if button in expectedActions:
            self.emit(SIGNAL('logMessage'), "Expected {0}, got {1}.".format(eaString, button), LogStyle.SUCCESS)
            
            if button == "R" and betsize and tc.gtype == "NL":        
                if (betsize == expectedBetsize or expectedBetsize == "Any"):          
                    self.emit(SIGNAL('logMessage'), "Expected R {0}, got R {1}.".format(expectedBetsize, betsize), LogStyle.SUCCESS)
                else:
                    self.emit(SIGNAL('logMessage'), "Expected R {0}, got R {1}.".format(expectedBetsize, betsize), LogStyle.ERROR)
                    self.testFailed = True       
        else:
            self.emit(SIGNAL('logMessage'), "Expected {0}, got {1}.".format(eaString, button), LogStyle.ERROR)
            self.testFailed = True
                
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

        
