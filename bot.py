'''Entry point'''
from getpass import getpass
import logging
from signal import signal, SIGINT
import sys

import discord
from discord.ext import tasks

from cogs.status import Status
from library import cards
from library.pagination import Paginator
from library.search import autocomplete, lookup

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
cardoption = discord.Option(str, 'Card name:', autocomplete=autocomplete)
mentionoption = discord.Option(discord.Member, 'Mention:', default=None)
publicoption = discord.Option(bool, 'Should the results be visible to everyone?', default=True)

@bot.slash_command()
async def search(
    ctx,
    card : cardoption,
    mention : mentionoption,
    public : publicoption
):
    '''Search for TCG/OCG/Skill cards'''
    if results := await lookup(card):
        paginator = Paginator([await result.make_embed() for result in results])
        await paginator.respond(ctx.interaction, ephemeral=not public)
        if mention:
            await ctx.respond(mention.mention)
    else:
        await ctx.respond(f'No cards found for search `{card}`', ephemeral=True)

@bot.slash_command()
async def rulings( # pylint: disable=too-many-arguments
    ctx,
    card : cardoption,
    question : discord.Option(str, 'Keywords:', default=''),
    index : discord.Option(int, name='qa', description='YGOrg Q&A ID:', default=0),
    mention : mentionoption,
    public : publicoption
):
    '''Search for rulings'''
    if result := await lookup(card, results=1):
        result = result.pop()
        await ctx.defer(ephemeral=not public)

        if results := await result.getrulings(question, index):
            paginator = Paginator(results)
            await paginator.respond(ctx.interaction, ephemeral=not public)
            if mention:
                await ctx.respond(mention.mention)
        else:
            await ctx.respond(f'`{result.name}` has no current rulings', ephemeral=not public)
    else:
        await ctx.respond(f'No card found for search `{card}`', ephemeral=True)

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
