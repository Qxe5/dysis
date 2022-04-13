'''Entry point'''
from getpass import getpass
import logging
from signal import signal, SIGINT
import sys

import discord
from discord.ext import tasks, pages

from cogs.status import Status
from library import cards
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
@bot.slash_command()
async def search(
    ctx,
    card : discord.Option(str, 'Card name:', autocomplete=autocomplete),
    public : discord.Option(bool, 'Should the results be visible to everyone?')
):
    '''Search for a TCG/OCG/Skill card'''
    if results := await lookup(card):
        paginator = pages.Paginator(results, timeout=0)
        await paginator.respond(ctx.interaction, ephemeral=not public)
    else:
        await ctx.respond(f'No cards found for search `{card}`', ephemeral=True)

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
