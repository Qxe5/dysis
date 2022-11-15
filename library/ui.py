'''UI'''
from contextlib import suppress

from discord import ui, SelectOption, Embed, Colour, NotFound

from library import score
from library.icons import TICK, CROSS, LOGO

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
    def __init__(self, author, options, ephemeral):
        '''
        Initialize the container with the state of who requested the container,
        the multiple choice options available to them,
        and whether they should be responded to publicly
        '''
        super().__init__(timeout=20)

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
        '''Handle no response'''
        if self.children:
            self.clear_items()
            user_score = await score.record(self.author.id, correct=False)

            with suppress(NotFound):
                await self.message.edit(
                    embeds=self.message.embeds + [
                        await mark_embed(
                            'N/A',
                            self.correct_answer,
                            user_score,
                            await score.rank(self.author.id)
                        )
                    ],
                    view=self
                )

class WhoSelect(ui.Select):
    '''A representation of a multiple choice selection'''
    async def callback(self, interaction):
        '''Respond to the interaction as to whether the input answer is correct'''
        if interaction.user == self.view.author:
            self.view.clear_items()
            await self.view.message.edit(view=self.view)

            await interaction.response.send_message(
                embed=await mark_embed(
                    self.values[0],
                    self.view.correct_answer,
                    await score.record(
                        interaction.user.id,
                        correct=self.values[0] == self.view.correct_answer
                    ),
                    await score.rank(interaction.user.id)
                ),
                ephemeral=self.view.ephemeral
            )
