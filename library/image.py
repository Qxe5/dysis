'''Image cache'''
import asyncio
from contextlib import suppress

import aiohttp

from library.api import ART, FIH

images = {}

async def fetch(client, cid):
    '''Rehost and return the main artwork image of the card with ID via the client'''
    key = '6d207e02198a847aa98d0a2a901485a5' # public

    with suppress(aiohttp.ClientConnectionError, aiohttp.ClientResponseError, asyncio.TimeoutError):
        async with client.get(f'{FIH}?key={key}&source={ART.substitute(cid=cid)}') as response:
            return (await response.json())['image']['url']

async def cache(cid):
    '''Cache the main artwork image of the card with ID'''
    async with aiohttp.ClientSession(raise_for_status=True) as client:
        images[cid] = await fetch(client, cid)

async def get(cid):
    '''Get and return the main artwork image of the card with ID'''
    if cid not in images:
        await cache(cid)

    return images[cid]
