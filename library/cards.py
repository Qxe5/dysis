'''Lookup table'''
import asyncio

import aiohttp

from library.card import Card

cards = {}

async def retrieve_card_data():
    '''Retrieve and return raw card data or None on error'''
    api = ('https://db.ygoprodeck.com/api/v7/cardinfo.php?'
           'misc=yes')

    async with aiohttp.ClientSession() as client:
        try:
            async with client.get(api) as response:
                if response.ok:
                    return (await response.json())['data']
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            return None

async def generatecards():
    '''Update lookup table'''
    if card_data := await retrieve_card_data():
        cards.clear()

        for card_datum in card_data:
            card = Card(card_datum)
            cards[card.name.lower()] = await card.make_embed()
