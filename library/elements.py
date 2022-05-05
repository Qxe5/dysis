'''Types of card elements'''
from collections import namedtuple

Levels = namedtuple('Levels', 'level scale link')
Stats = namedtuple('Stats', 'attack defence')
Limits = namedtuple('Limits', 'tcg ocg')
Releases = namedtuple('Releases', 'tcg ocg')
Prices = namedtuple('Prices', 'cardmarket tcgplayer')
Set = namedtuple('Set', 'id name rarityid rarity price')

Pendulum = namedtuple('Pendulum', 'pendulum monster flavour')
