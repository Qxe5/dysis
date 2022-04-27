'''Lookup table'''
import asyncio

import aiohttp

from library.api import YGORG, YGOPRO
from library.card import Card
from library.collection import koids, cards

async def retrieve_card_data():
    '''Retrieve and return raw card data or None on error'''
    ygorg = f'{YGORG}data/idx/card/name/en'
    ygopro = f'{YGOPRO}cardinfo.php?misc=yes'

    async with aiohttp.ClientSession(raise_for_status=True) as client:
        try:
            async with client.get(ygorg) as ygorgresponse, client.get(ygopro) as ygoproresponse:
                return (await ygorgresponse.json(), (await ygoproresponse.json())['data'])
        except (aiohttp.ClientConnectionError, aiohttp.ClientResponseError, asyncio.TimeoutError):
            return None

async def generatecards():
    '''Update lookup table'''
    if card_data := await retrieve_card_data():
        koids.clear()
        cards.clear()

        koid_data, card_data = card_data

        for card, kids in koid_data.items():
            koids[card] = max(kids)

            if len(kids) > 1:
                koids[f'{card} (Skill Card)'] = min(kids)

        koids.update({koid : card for card, koid in koids.items()})

        for card_datum in card_data:
            card = Card(card_datum)
            cards[card.name.lower()] = card
