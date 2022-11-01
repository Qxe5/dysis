'''Card updates'''
import asyncio

import aiohttp

from library.api import YGOPRO
from library.card import Card
from library.collection import cards, koids

async def retrieve_card_data():
    '''Retrieve and return raw card data or None on error'''
    ygopro = f'{YGOPRO}cardinfo.php?misc=yes'

    async with aiohttp.ClientSession(raise_for_status=True) as client:
        try:
            async with client.get(ygopro) as response:
                return (await response.json())['data']
        except (aiohttp.ClientConnectionError, aiohttp.ClientResponseError, asyncio.TimeoutError):
            return None

async def generatecards():
    '''Update lookup table'''
    if card_data := await retrieve_card_data():
        cards.clear()
        koids.clear()

        for card_datum in card_data:
            card = Card(card_datum)
            cards[card.name.lower()] = card
            koids[card.koid] = card.name
