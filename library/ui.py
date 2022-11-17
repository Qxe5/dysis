'''UI'''
from contextlib import suppress

from discord import ui, SelectOption, ButtonStyle, Embed, Colour, NotFound

from library import score
from library.icons import TICK, CROSS, LOGO
from library.search import lookup

async def mark_embed(answer, correct_answer, user_score, rank):
    '''
    Make and return an embed depicting if the answer provided matches the correct answer,
    the user's score, and their rank
    '''
    correct = answer == correct_answer
    wins, losses = user_score
    rank, players = rank

    embed = Embed(colour=Colour.green() if correct else Colour.brand_red())
    embed.set_author(
        icon_url=TICK if correct else CROSS,
        name='Correct' if correct else 'Incorrect'
    )
    embed.add_field(name='Your Answer', value=answer)
    if not correct:
        embed.add_field(name='Correct Answer', value=correct_answer, inline=False)

    embed.set_footer(
        icon_url=LOGO,
        text=f'Win Rate: {await score.percent(wins, losses)} ({wins} - {losses})\n'
             f'Score: {await score.points(wins, losses)}\n'
             f'Rank: {rank} / {players}'
    )

    return embed

class Who(ui.View):
    '''A representation of a container for UI items'''
    def __init__(self, author, options, ephemeral, **kwargs):
        '''
        Initialize the container with the state of who requested the container,
        the multiple choice options available to them,
        and whether they should be responded to publicly
        '''
        super().__init__(**kwargs)
        self.author = author
        self.options = options
        self.answer = [name for name, correct in options.items() if correct].pop()
        self.ephemeral = ephemeral

    async def interaction_check(self, interaction):
        '''Determine and return if the interaction should be responded to'''
        return interaction.user == self.author

    async def on_timeout(self):
        '''Handle no response'''
        if self.children:
            self.clear_items()
            user_score = await score.record(self.author.id, correct=False)

            with suppress(NotFound):
                await self.message.edit(
                    embeds=self.message.embeds + [
                        await mark_embed(
                            'N/A',
                            self.answer,
                            user_score,
                            await score.rank(self.author.id)
                        )
                    ],
                    view=self
                )

class WhoEasy(Who):
    '''A representation of an easy game'''
    def __init__(self, *args, **kwargs):
        '''Initialize an easy game'''
        super().__init__(*args, **kwargs)
        self.add_item(WhoSelect(options=[SelectOption(label=option) for option in self.options]))

class WhoSelect(ui.Select):
    '''A representation of a multiple choice selection'''
    async def callback(self, interaction):
        '''Respond to the interaction as to whether the input answer is correct'''
        self.view.clear_items()
        await self.view.message.edit(view=self.view)

        await interaction.response.send_message(
            embed=await mark_embed(
                self.values[0],
                self.view.answer,
                await score.record(
                    interaction.user.id,
                    correct=self.values[0] == self.view.answer
                ),
                await score.rank(interaction.user.id)
            ),
            ephemeral=self.view.ephemeral
        )

class WhoHard(Who):
    '''A representation of a hard game'''
    @ui.button(label='Answer', style=ButtonStyle.primary)
    async def callback(self, _, interaction):
        '''Respond to the interaction with a modal'''
        await interaction.response.send_modal(WhoModal(self, self.answer))

class WhoModal(ui.Modal):
    '''A representation of an input modal'''
    def __init__(self, view, answer):
        '''Initialize the input modal with the view and the answer'''
        super().__init__(title='What is the name of this card?')
        self.view = view
        self.answer = answer
        self.add_item(ui.InputText(label='Answer'))

    async def callback(self, interaction):
        '''Respond to the interaction as to whether the input answer is correct'''
        if self.view.is_finished():
            await interaction.response.defer()
        else:
            self.view.clear_items()
            await self.view.message.edit(view=self.view)
            answer = (await lookup(self.children[0].value, 'CG', results=1)).pop().name

            await interaction.response.send_message(
                embed=await mark_embed(
                    answer,
                    self.answer,
                    await score.record(
                        interaction.user.id,
                        correct=answer == self.answer,
                        difficulty='Hard'
                    ),
                    await score.rank(interaction.user.id)
                ),
                ephemeral=self.view.ephemeral
            )
