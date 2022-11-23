'''UI'''
from contextlib import suppress
from dataclasses import dataclass
from time import time

from discord import ui, SelectOption, ButtonStyle, Embed, Colour, NotFound

from library import score
from library.icons import TICK, CROSS, GREEN_DOT, RED_DOT, LOGO
from library.search import lookup

EASYWINS = 1
HARDWINS = 10

@dataclass
class AnswerSheet:
    '''A representation of an answer sheet used for marking and display'''
    answer : str
    correct_answer : str
    user_score : tuple
    rank : tuple
    timetaken : float
    increment : int = -1

async def mark_embed(answersheet):
    '''Make and return an embed depicting the marked answer sheet'''
    correct = answersheet.answer == answersheet.correct_answer
    wins, losses = answersheet.user_score
    rank, players = answersheet.rank
    trophy = (' 🏆' if correct
                    and answersheet.increment in {wins * 2 for wins in (EASYWINS, HARDWINS)}
                    else '')

    embed = Embed(
        colour=Colour.green() if correct else Colour.brand_red(),
        description=f'{GREEN_DOT}{answersheet.increment:+}' if correct else f'{RED_DOT}{-1}'
    )

    embed.set_author(
        icon_url=TICK if correct else CROSS,
        name='Correct' if correct else 'Incorrect'
    )

    embed.add_field(name='Your Answer', value=answersheet.answer)
    if not correct:
        embed.add_field(name='Correct Answer', value=answersheet.correct_answer, inline=False)

    embed.add_field(
        name='Time',
        value=f'{answersheet.timetaken:.2f}s{trophy}',
        inline=False
    )

    embed.set_footer(
        icon_url=LOGO,
        text=f'Win Rate: {await score.percent(wins, losses)} ({wins} - {losses})\n'
             f'Points: {await score.points(wins, losses)}\n'
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
        self.time = time()
        self.ephemeral = ephemeral

    async def interaction_check(self, interaction):
        '''Determine and return if the interaction should be responded to without error'''
        return interaction.user == self.author

    async def on_check_failure(self, interaction):
        '''Respond to unknown authors'''
        await interaction.response.send_message(
            f'Only {self.author} can interact with this item. Please run the command yourself.',
            ephemeral=True,
            delete_after=10
        )

    async def on_timeout(self):
        '''Handle no response'''
        if self.children:
            self.clear_items()
            user_score = await score.record(self.author.id, correct=False)

            with suppress(NotFound):
                await self.message.edit(
                    embeds=self.message.embeds + [
                        await mark_embed(
                            AnswerSheet(
                                'N/A',
                                self.answer,
                                user_score,
                                await score.rank(self.author.id),
                                timetaken=30
                            )
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

        timetaken = time() - self.view.time
        increment = EASYWINS if timetaken > 5 else EASYWINS * 2

        await interaction.response.send_message(
            embed=await mark_embed(
                AnswerSheet(
                    self.values[0],
                    self.view.answer,
                    await score.record(
                        interaction.user.id,
                        correct=self.values[0] == self.view.answer,
                        increment=increment
                    ),
                    await score.rank(interaction.user.id),
                    timetaken,
                    increment
                )
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
        super().__init__(title='What is the full name of this card?')
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
            timetaken = time() - self.view.time
            increment = HARDWINS if timetaken > 15 else HARDWINS * 2

            await interaction.response.send_message(
                embed=await mark_embed(
                    AnswerSheet(
                        answer,
                        self.answer,
                        await score.record(
                            interaction.user.id,
                            correct=answer == self.answer,
                            increment=increment
                        ),
                        await score.rank(interaction.user.id),
                        timetaken,
                        increment
                    )
                ),
                ephemeral=self.view.ephemeral
            )
