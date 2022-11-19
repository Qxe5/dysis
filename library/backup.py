'''Backup'''
import os

from discord import File

async def send(bot):
    '''Send the backup to the set channel'''
    key = 'CHANNEL'

    if key in os.environ:
        channel = await bot.fetch_channel(os.environ[key])
        if channel:
            await channel.purge()

            path = 'cache/scores'
            if os.path.exists(path):
                with open(path, 'rb') as scores:
                    await channel.send(file=File(scores, filename='scores'))
