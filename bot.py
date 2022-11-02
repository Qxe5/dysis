'''Entry point'''
from getpass import getpass
import logging
from signal import signal, SIGINT
import sys

import discord
from discord.ext import tasks

from cogs.status import Status
from library import cards, helper
from library.pagination import Paginator
from library.search import lookup

signal(SIGINT, lambda signalnumber, stackframe: sys.exit())
logging.basicConfig()

# init
bot = discord.Bot()

@bot.listen()
async def on_ready():
    '''Print info when ready'''
    print('Logged in as', bot.user)

# tasks
@tasks.loop(hours=24)
async def updatecards():
    '''Update lookup table'''
    await cards.generatecards()

updatecards.start()

# commands
@bot.slash_command(checks=[helper.check_view_read])
async def search(
    ctx,
    card : helper.cardoption,
    cardtype : helper.cardtype_option,
    mention : helper.mentionoption,
    public : helper.publicoption
):
    '''Search for TCG/OCG/Skill cards'''
    if results := await lookup(card, cardtype):
        paginator = Paginator([await result.make_embed() for result in results])
        await paginator.respond(ctx.interaction, ephemeral=not public)
        await helper.ping(ctx, mention, not public)
    else:
        await helper.noresult(ctx, card)

@search.error
async def search_error(ctx, error):
    '''Handle a lack of channel permissions'''
    if isinstance(error, discord.CheckFailure):
        await helper.no_view_read(ctx)
    else:
        raise error

@bot.slash_command(checks=[helper.check_view_read])
async def arts(
    ctx,
    card : helper.cardoption,
    cardtype : helper.cardtype_option,
    mention : helper.mentionoption,
    public : helper.publicoption
):
    '''Search for card arts'''
    if result := await lookup(card, cardtype, results=1):
        result = result.pop()

        paginator = Paginator(await result.make_art_embeds())
        await paginator.respond(ctx.interaction, ephemeral=not public)
        await helper.ping(ctx, mention, not public)
    else:
        await helper.noresult(ctx, card)

@arts.error
async def arts_error(ctx, error):
    '''Handle a lack of channel permissions'''
    if isinstance(error, discord.CheckFailure):
        await helper.no_view_read(ctx)
    else:
        raise error

@bot.slash_command(checks=[helper.check_view_read])
async def sets(
    ctx,
    card : helper.cardoption,
    cardtype : helper.cardtype_option,
    mention : helper.mentionoption,
    public : helper.publicoption
):
    '''Search for card sets'''
    if result := await lookup(card, cardtype, results=1):
        result = result.pop()

        if embeds := await result.make_set_embeds():
            paginator = Paginator(embeds)
            await paginator.respond(ctx.interaction, ephemeral=not public)
            await helper.ping(ctx, mention, not public)
        else:
            await helper.noattribute(ctx, result.name, 'sets', not public)
    else:
        await helper.noresult(ctx, card)

@sets.error
async def sets_error(ctx, error):
    '''Handle a lack of channel permissions'''
    if isinstance(error, discord.CheckFailure):
        await helper.no_view_read(ctx)
    else:
        raise error

@bot.slash_command(checks=[helper.check_view_read])
async def setimages(
    ctx,
    card : helper.cardoption,
    cardtype : helper.cardtype_option,
    mention : helper.mentionoption,
    public : helper.publicoption
):
    '''Search for card set images'''
    if result := await lookup(card, cardtype, results=1):
        result = result.pop()

        if embeds := await result.make_setimage_embeds():
            paginator = Paginator(embeds)
            await paginator.respond(ctx.interaction, ephemeral=not public)
            await helper.ping(ctx, mention, not public)
        else:
            await helper.noattribute(ctx, result.name, 'set images', not public)
    else:
        await helper.noresult(ctx, card)

@setimages.error
async def setimages_error(ctx, error):
    '''Handle a lack of channel permissions'''
    if isinstance(error, discord.CheckFailure):
        await helper.no_view_read(ctx)
    else:
        raise error

@bot.slash_command(checks=[helper.check_view_read])
async def rulings( # pylint: disable=too-many-arguments
    ctx,
    card : helper.cardoption,
    cardtype : helper.cardtype_option,
    question : discord.Option(str, 'Keywords:', default=''),
    index : discord.Option(int, name='qa', description='YGOrg Q&A ID:', default=0),
    mention : helper.mentionoption,
    public : helper.publicoption
):
    '''Search for rulings'''
    if result := await lookup(card, cardtype, results=1):
        result = result.pop()
        await ctx.defer(ephemeral=not public)

        if results := await result.getrulings(question, index):
            paginator = Paginator(results)
            await paginator.respond(ctx.interaction, ephemeral=not public)
            await helper.ping(ctx, mention, not public)
        else:
            await helper.noattribute(ctx, result.name, 'rulings', not public)
    else:
        await helper.noresult(ctx, card)

@rulings.error
async def rulings_error(ctx, error):
    '''Handle a lack of channel permissions'''
    if isinstance(error, discord.CheckFailure):
        await helper.no_view_read(ctx)
    else:
        raise error

@bot.slash_command()
async def servers(ctx):
    '''Get the server count of the bot'''
    await ctx.respond(
        f'{len(bot.guilds)} Servers ({sum(guild.member_count for guild in bot.guilds)} Members)',
        ephemeral=True
    )

# cogs
bot.add_cog(Status(bot))

# authenticate
try:
    bot.run(getpass('Token: '))
except discord.LoginFailure as loginfailure:
    print('Invalid Token')
    raise SystemExit(1) from loginfailure
