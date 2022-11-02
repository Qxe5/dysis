'''Command helper'''
from discord import Option, Member, PartialMessageable

from library.search import autocomplete

cardoption = Option(str, 'Card name:', autocomplete=autocomplete)
cardtype_option = Option(
    str,
    'Card Type:',
    choices=['Monster', 'Spell', 'Trap', 'Token', 'Skill'],
    default='All'
)
mentionoption = Option(Member, 'Mention:', default=None)
publicoption = Option(bool, 'Should the results be visible to everyone?', default=True)

async def check_view_read(ctx):
    '''
    Check and return if the bot has the View Channels
    and Read Message History channel permissions
    '''
    if isinstance(ctx.channel, PartialMessageable):
        return True

    permissions = ctx.channel.permissions_for(ctx.guild.get_member(ctx.bot.user.id))

    return permissions.view_channel and permissions.read_message_history

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
