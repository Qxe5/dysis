'''Image cache'''
from library.api import FIH

images = {}

async def fetch(client, card):
    '''Rehost and return the main artwork image of the card via the client'''
    key = '6d207e02198a847aa98d0a2a901485a5' # public

    async with client.get(f'{FIH}?key={key}&source={await card.art()}', timeout=5) as response:
        return (await response.json())['image']['url']

async def cache(client, card):
    '''Cache the main artwork image of the card via the client'''
    cid = await card.getid()

    if cid not in images:
        images[cid] = await fetch(client, card)

async def get(cid):
    '''Get and return the main artwork image of the card with ID'''
    return images[cid]
