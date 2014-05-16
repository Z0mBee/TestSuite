import configparser

def parse_actions(config_text):
        actions = []
        for act in config_text.split(','):
            act = act.strip()
            act = act.split(' ')
            actions.append([a.strip() for a in act])
        return actions


config = configparser.SafeConfigParser()
config.read("testcases/testcase1.txt")

pf_actions = parse_actions(config.get('preflop', 'actions'))
print(pf_actions)
#===============================================================================
#         self.hand = [c.strip() for c in config.get('preflop', 'hand').split(',')]
# 
#         try:
#             self.flop_actions = self._parse_actions(config.get('flop', 'actions'))
#             self.fc = [c.strip() for c in config.get('flop', 'cards').split(',')]
#         except:
#             self.flop_actions = []
#             self.fc = None
#===============================================================================