'''Card searching'''
import asyncio
from difflib import get_close_matches
from random import choice

import aiohttp

from library.api import ART
from library.collection import cards, monsters, spells, traps, tokens, skills

DEFAULT_RESULTS = 25

async def cardpool(cardtype):
    '''Return the card pool given a card type'''
    match cardtype:
        case 'All':
            return cards.keys()
        case 'Monster':
            return monsters
        case 'Spell':
            return spells
        case 'Trap':
            return traps
        case 'Token':
            return tokens
        case 'Skill':
            return skills

async def fuzzy(comparate, comparables, results=DEFAULT_RESULTS):
    '''Compare the comparate with the comparables and return results'''
    return get_close_matches(comparate, comparables, cutoff=0.1, n=results)

async def autocomplete(ctx):
    '''Return autocompletions from a current search term'''
    term = ctx.options['card'].lower()

    return await fuzzy(term, [
            card for card in await cardpool(ctx.options['cardtype']) if term in card
        ]
    ) if term else []

async def lookup(term, cardtype, results=DEFAULT_RESULTS):
    '''
    Lookup a search term in the lookup table given a card type,
    and return the closest results or None
    '''
    if matches := await fuzzy(term.lower(), await cardpool(cardtype), results):
        return [cards[match] for match in matches]

async def getoptions(number=4):
    '''Get and return a number of multiple choice options'''
    options = []

    while len(options) != number:
        possible = cards[choice(tuple(cards.keys()))]

        if possible not in options:
            async with aiohttp.ClientSession(raise_for_status=True) as client:
                try:
                    async with client.get(ART.substitute(cid=possible.ids[0])):
                        options.append(possible)
                except (
                    aiohttp.ClientConnectionError,
                    aiohttp.ClientResponseError,
                    asyncio.TimeoutError
                ):
                    pass

    correct = choice(options)

    return {
        option.name : await option.make_who_embed() if option is correct else None
        for option in options
    }
