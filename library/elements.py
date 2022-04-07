'''Types of card elements'''
from collections import namedtuple

Levels = namedtuple('Levels', 'level scale link')
Stats = namedtuple('Stats', 'attack defence')
Limits = namedtuple('Limits', 'tcg ocg')
Releases = namedtuple('Releases', 'tcg ocg')
Prices = namedtuple('Prices', 'cardmarket tcgplayer')

Pendulum = namedtuple('Pendulum', 'pendulum monster flavour')
