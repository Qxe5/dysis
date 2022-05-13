'''Pagination'''
from contextlib import suppress

from discord import NotFound, Forbidden, HTTPException
from discord.ext import pages

class Paginator(pages.Paginator):
    '''A representation of a paginator'''
    async def on_timeout(self):
        '''Disable the buttons'''
        for button in self.children:
            button.disabled = True

        with suppress(NotFound, Forbidden, HTTPException):
            await self.message.edit(view=self)
