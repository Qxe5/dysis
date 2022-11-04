'''UI'''
from discord import ui, SelectOption, Embed, Colour, NotFound

from library.icons import TICK, CROSS

async def mark_embed(answer, correct_answer):
    '''Make and return an embed portraying if the answer provided matches the correct answer'''
    correct = answer == correct_answer

    embed = Embed(colour=Colour.green() if correct else Colour.dark_red())
    embed.set_author(
        icon_url=TICK if correct else CROSS,
        name='Correct' if correct else 'Incorrect'
    )
    embed.add_field(name='Your Answer', value=answer)
    if not correct:
        embed.add_field(name='Correct Answer', value=correct_answer, inline=False)

    return embed

class Who(ui.View):
    '''A representation of a container for UI items'''
    def __init__(self, author, options, ephemeral):
        '''
        Initialize the container with the state of who requested the container,
        the multiple choice options available to them,
        and whether they should be responded to publicly
        '''
        super().__init__(timeout=30)

        self.author = author
        self.ephemeral = ephemeral

        for name, correct in options.items():
            if correct:
                self.correct_answer = name
                break

        self.add_item(
            WhoSelect(options=[SelectOption(label=option) for option in options])
        )

    async def on_timeout(self):
        '''Delete the items in the view'''
        if self.children:
            self.clear_items()

            try:
                await self.message.edit(
                    embeds=self.message.embeds + [await mark_embed('N/A', self.correct_answer)],
                    view=self
                )
            except NotFound:
                pass

class WhoSelect(ui.Select):
    '''A representation of a multiple choice selection'''
    async def callback(self, interaction):
        '''Respond to the interaction as to whether the input answer is correct'''
        if interaction.user == self.view.author:
            self.view.clear_items()
            await self.view.message.edit(view=self.view)

            await interaction.response.send_message(
                embed=await mark_embed(self.values[0], self.view.correct_answer),
                ephemeral=self.view.ephemeral
            )
