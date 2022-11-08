'''Score management'''
from math import ceil
import shelve

from discord import Embed, Colour

from library.icons import GOLD, SILVER, BRONZE, BACKGROUND, LOGO

PATH = 'cache/scores'

async def derive(wins, losses):
    '''Derive a win rate from the wins and losses and return it'''
    return wins / (wins + losses)

async def percent(wins, losses):
    '''Format a win lose ratio as a percent and return it'''
    return f'{await derive(wins, losses) * 100:.2f}%'

async def record(user, correct):
    '''Update the users score based off whether they were correct and return it'''
    user = str(user)

    with shelve.open(PATH) as scores:
        if user not in scores:
            scores[user] = (1, 0) if correct else (0, 1)
        else:
            wins, losses = scores[user]
            scores[user] = (wins + 1, losses) if correct else (wins, losses + 1)

        return scores[user]

async def rankings():
    '''
    Calculate and return the rankings of all players,
    whose elements are (snowflake, wins, losses, score)
    '''
    ranks = []

    with shelve.open(PATH) as scores:
        for user, score in scores.items():
            wins, losses = score
            score = ceil(await derive(wins, losses) * max(wins - losses, 0))
            ranks.append((user, wins, losses, score))

    return sorted(ranks, key=lambda entry: entry[3], reverse=True)

async def leaderboard(bot):
    '''Make and return the leaderboard'''
    top = 20
    ranks = (await rankings())[:top]

    embeds = []
    medals = [BRONZE, SILVER, GOLD]

    for user, wins, losses, score in ranks:
        user = await bot.fetch_user(user)

        embed = Embed(
            colour=user.accent_colour if user.accent_colour else Colour.default(),
            description=user.mention
        )
        embed.set_author(icon_url=user.display_avatar, name=f'Rank #{len(embeds) + 1}')
        if medals:
            embed.set_thumbnail(url=medals.pop())
        embed.add_field(name='Wins', value=wins)
        embed.add_field(name='Losses', value=losses)
        embed.add_field(name='Win Rate', value=await percent(wins, losses))
        embed.add_field(name='Score', value=score)
        embed.set_image(url=user.banner if user.banner else BACKGROUND)
        embed.set_footer(icon_url=LOGO, text=user)

        embeds.append(embed)

    return embeds
