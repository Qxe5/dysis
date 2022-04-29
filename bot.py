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
@bot.slash_command()
async def search(
    ctx,
    card : helper.cardoption,
    mention : helper.mentionoption,
    public : helper.publicoption
):
    '''Search for TCG/OCG/Skill cards'''
    if results := await lookup(card):
        paginator = Paginator([await result.make_embed() for result in results])
        await paginator.respond(ctx.interaction, ephemeral=not public)
        await helper.ping(ctx, mention, not public)
    else:
        await helper.noresult(ctx, card)

@bot.slash_command()
async def rulings( # pylint: disable=too-many-arguments
    ctx,
    card : helper.cardoption,
    question : discord.Option(str, 'Keywords:', default=''),
    index : discord.Option(int, name='qa', description='YGOrg Q&A ID:', default=0),
    mention : helper.mentionoption,
    public : helper.publicoption
):
    '''Search for rulings'''
    if result := await lookup(card, results=1):
        result = result.pop()
        await ctx.defer(ephemeral=not public)

        if results := await result.getrulings(question, index):
            paginator = Paginator(results)
            await paginator.respond(ctx.interaction, ephemeral=not public)
            await helper.ping(ctx, mention, not public)
        else:
            await ctx.respond(f'`{result.name}` has no current rulings', ephemeral=not public)
    else:
        await helper.noresult(ctx, card)

@bot.slash_command()
async def arts(
    ctx,
    card : helper.cardoption,
    mention : helper.mentionoption,
    public : helper.publicoption
):
    '''Search for card arts'''
    if result := await lookup(card, results=1):
        result = result.pop()

        paginator = Paginator(await result.make_art_embeds())
        await paginator.respond(ctx.interaction, ephemeral=not public)
        await helper.ping(ctx, mention, not public)
    else:
        await helper.noresult(ctx, card)

@bot.slash_command()
async def servers(ctx):
    '''Get the server count of the bot'''
    await ctx.respond(f'{len(bot.guilds)} Servers', ephemeral=True)

# cogs
bot.add_cog(Status(bot))

# authenticate
try:
    bot.run(getpass('Token: '))
except discord.LoginFailure as loginfailure:
    print('Invalid Token')
    raise SystemExit(1) from loginfailure
