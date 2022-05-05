'''Command helper'''
from discord import Option, Member

from library.search import autocomplete

cardoption = Option(str, 'Card name:', autocomplete=autocomplete)
mentionoption = Option(Member, 'Mention:', default=None)
publicoption = Option(bool, 'Should the results be visible to everyone?', default=True)

async def no_view_read(ctx):
    '''Handle a lack of the View Channels or Read Message History channel permissions'''
    await ctx.respond(
        'I need the `View Channels` and `Read Message History` permissions in this channel',
        ephemeral=True
    )

async def ping(ctx, member, ephemeral):
    '''Mention a member'''
    if member and not ephemeral:
        await ctx.respond(member.mention)

async def noresult(ctx, term):
    '''Handle a lack of search results given a search term'''
    await ctx.respond(f'No cards found for search `{term}`', ephemeral=True)

async def noattribute(ctx, card, attribute, ephemeral):
    '''Handle a lack of a card attribute'''
    await ctx.respond(f'`{card}` has no current {attribute}', ephemeral=ephemeral)
