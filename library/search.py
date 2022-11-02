'''Card searching'''
from difflib import get_close_matches

from library.collection import cards, monsters, spells, traps, tokens, skills

DEFAULT_RESULTS = 25

async def fuzzy(comparate, comparables, results=DEFAULT_RESULTS):
    '''Compare the comparate with the comparables and return results'''
    return get_close_matches(comparate, comparables, cutoff=0.1, n=results)

async def autocomplete(ctx):
    '''Return autocompletions from a current search term'''
    term = ctx.options['card'].lower()

    match ctx.options['cardtype']:
        case 'All':
            cardpool = cards.keys()
        case 'Monster':
            cardpool = monsters
        case 'Spell':
            cardpool = spells
        case 'Trap':
            cardpool = traps
        case 'Token':
            cardpool = tokens
        case 'Skill':
            cardpool = skills

    return await fuzzy(term, [
            card for card in cardpool if term in card
        ]
    ) if term else []

async def lookup(term, results=DEFAULT_RESULTS):
    '''Lookup a search term in the lookup table and return the closest results or None'''
    if matches := await fuzzy(term.lower(), cards.keys(), results):
        return [cards[match] for match in matches]
