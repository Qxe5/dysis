'''Card searching'''
import asyncio
from difflib import get_close_matches
from random import sample, choice
from string import punctuation

import aiohttp

from library.collection import cards, monsters, spells, traps, tokens, skills

DEFAULT_RESULTS = 25

async def clean(text):
    '''Remove punctuation and unicode from the text, convert it to lowercase and return it'''
    return (
        ' '.join(text.translate(str.maketrans({mark : ' ' for mark in punctuation})).split())
           .encode('ascii', 'ignore')
           .decode()
           .lower()
    )

async def cardpool(cardtype):
    '''Return the card pool given a card type'''
    return {
        'All'     : cards.keys(),
        'CG'      : cards.keys() - skills,
        'Monster' : monsters,
        'Spell'   : spells,
        'Trap'    : traps,
        'Token'   : tokens,
        'Skill'   : skills
    }[cardtype]

async def fuzzy(comparate, comparables, results=DEFAULT_RESULTS):
    '''Compare the comparate with the comparables and return results'''
    return get_close_matches(comparate, comparables, cutoff=0.1, n=results)

async def autocomplete(ctx):
    '''Return autocompletions from a current search term'''
    term = await clean(ctx.options['card'])

    return await fuzzy(term, [
            card for card in await cardpool(ctx.options['cardtype']) if term in card
        ]
    ) if term else []

async def lookup(term, cardtype, results=DEFAULT_RESULTS):
    '''
    Lookup a search term in the lookup table given a card type,
    and return the closest results or None
    '''
    if matches := await fuzzy(await clean(term), await cardpool(cardtype), results):
        return [cards[match] for match in matches]

async def getoptions(number=4, retries=8):
    '''Get and return a number of multiple choice options, or None on image API failure'''
    while retries:
        options = sample(
            tuple(card for card in cards.values() if card.type != 'Skill Card'),
            number
        )
        correct = choice(options)

        async with aiohttp.ClientSession(raise_for_status=True) as client:
            try:
                await client.head(await correct.make_art())
            except (
                aiohttp.ClientConnectionError,
                aiohttp.ClientResponseError,
                asyncio.TimeoutError
            ):
                retries -= 1
                continue

        return {
            option.name : await option.make_who_embed() if option is correct else None
            for option in options
        }
