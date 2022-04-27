'''Pagination'''
from contextlib import suppress

from discord import NotFound
from discord.ext import pages

class Paginator(pages.Paginator):
    '''A representation of a paginator'''
    async def on_timeout(self):
        '''Disable the buttons'''
        for button in self.children:
            button.disabled = True

        if self.message:
            with suppress(NotFound):
                await self.message.edit(view=self)
