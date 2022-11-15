'''Card updates'''
import asyncio

import aiohttp

from library.api import YGOPRO
from library.card import Card
from library.collection import cards, koids, monsters, spells, traps, tokens, skills
from library.search import clean

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
        for collection in (cards, koids, monsters, spells, traps, tokens, skills):
            collection.clear()

        for card_datum in card_data:
            card = Card(card_datum)
            name = await clean(card.name)
            cards[name] = card
            koids[card.koid] = card.name

            if 'Monster' in card.type:
                monsters.add(name)
            elif 'Spell' in card.type:
                spells.add(name)
            elif 'Trap' in card.type:
                traps.add(name)
            elif 'Token' in card.type:
                tokens.add(name)
            elif 'Skill' in card.type:
                skills.add(name)
