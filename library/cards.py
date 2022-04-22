'''Lookup table'''
import asyncio

import aiohttp

from library.card import YGORGAPI, koids, Card

cards = {}

async def retrieve_card_data():
    '''Retrieve and return raw card data or None on error'''
    ygorg = f'{YGORGAPI}data/idx/card/name/en'
    ygopro = 'https://db.ygoprodeck.com/api/v7/cardinfo.php?misc=yes'

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
