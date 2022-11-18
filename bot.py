'''Entry point'''
from getpass import getpass
from logging import basicConfig
from random import choice
from signal import signal, SIGINT
import sys

import discord
from discord.ext import tasks

from cogs.status import Status
from library import cards, score, helper
from library.pagination import Paginator
from library.search import lookup, cardpool, getoptions
from library.ui import WhoEasy, WhoHard

signal(SIGINT, lambda signalnumber, stackframe: sys.exit())
basicConfig()

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

randomgroup = bot.create_group(name='random')

@randomgroup.command(name='card', checks=[helper.check_view_read])
async def randomcard(
    ctx,
    cardtype : helper.cardtype_option,
    mention : helper.mentionoption,
    public : helper.publicoption
):
    '''Get a random card'''
    await ctx.invoke(
        bot.get_command('search'),
        card=choice(tuple(await cardpool(cardtype))),
        cardtype=cardtype,
        mention=mention,
        public=public
    )

@randomgroup.command(checks=[helper.check_view_read])
async def art(
    ctx,
    cardtype : helper.cardtype_option,
    mention : helper.mentionoption,
    public : helper.publicoption
):
    '''Get a random card art'''
    await ctx.invoke(
        bot.get_command('arts'),
        card=choice(tuple(await cardpool(cardtype))),
        cardtype=cardtype,
        mention=mention,
        public=public
    )

async def art_error(ctx, error):
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

@bot.slash_command()
async def who(
    ctx,
    difficulty : discord.Option(
        str,
        'Difficulty:',
        choices=['Easy', 'Hard'],
        default='Easy'
    ),
    mention : helper.mentionoption,
    public : helper.publicoption
):
    '''Get a trivia question'''
    if options := await getoptions():
        args = (ctx.author, options, not public)
        kwargs = {'timeout' : 30}

        await ctx.respond(
            embed=[embed for embed in options.values() if embed].pop(),
            view=WhoEasy(*args, **kwargs) if difficulty == 'Easy' else WhoHard(*args, **kwargs),
            ephemeral=not public
        )
        await helper.ping(ctx, mention, not public)
    else:
        await ctx.respond('Failed to get the image. Please try again later.', ephemeral=not public)

@bot.slash_command(checks=[helper.check_view_read])
async def leaderboard(
    ctx,
    mention : helper.mentionoption,
    public : helper.publicoption
):
    '''Get the trivia leaderboard'''
    await ctx.defer(ephemeral=not public)

    if ranks := await score.leaderboard(bot):
        paginator = Paginator(ranks)
        await paginator.respond(ctx.interaction, ephemeral=not public)
        await helper.ping(ctx, mention, not public)
    else:
        await ctx.respond(
            'There is no leaderboard at this time. Be the first!',
            ephemeral=not public
        )

@bot.slash_command()
async def servers(ctx):
    '''Get the server count of the bot'''
    await ctx.respond(
        f'{len(bot.guilds)} Servers ({sum(guild.member_count for guild in bot.guilds)} Members)',
        ephemeral=True
    )

@search.error
@arts.error
@sets.error
@setimages.error
@rulings.error
@randomcard.error
@art.error
async def channel_error(ctx, error):
    '''Handle a lack of channel permissions'''
    if isinstance(error, discord.CheckFailure):
        await helper.no_view_read(ctx)
    else:
        raise error

# cogs
bot.add_cog(Status(bot))

# authenticate
try:
    bot.run(getpass('Token: '))
except discord.LoginFailure as loginfailure:
    print('Invalid Token')
    raise SystemExit(1) from loginfailure
