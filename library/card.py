'''JSON to Object mapping'''
import asyncio
from contextlib import suppress
from datetime import datetime, timedelta
from io import StringIO
from json import dumps, loads
from os import remove
from os.path import exists
from re import findall
from string import Template
from urllib.parse import quote

import aiohttp
from discord import Embed, Colour
from discord.utils import format_dt

from library import colours, icons
from library.api import ART, YGOPRICES, YGORG
from library.collection import cards, koids
from library.elements import Levels, Stats, Limits, Releases, Prices, Set, Pendulum

ygoprices = Template('https://yugiohprices.com/browse_sets?set=$set')

def extract_koid(card):
    '''Extract and return the KOID or None from the card JSON'''
    misc = card['misc_info'][0]
    return misc['konami_id'] if 'konami_id' in misc else None

def extract_stats(card):
    '''Extract and return the stats from the card JSON'''
    stats = []

    stats.append(card['atk'] if 'atk' in card else None)
    stats.append(card['def'] if 'def' in card else None)

    misc = card['misc_info'][0]
    if 'question_atk' in misc:
        stats[0] = '?'
    if 'question_def' in misc:
        stats[1] = '?'

    return Stats(stats[0], stats[1])

def extract_releases(card):
    '''Extract and return the releases from the card JSON'''
    releases = []

    misc = card['misc_info'][0]
    releases.append(misc['tcg_date'] if 'tcg_date' in misc else None)
    releases.append(misc['ocg_date'] if 'ocg_date' in misc else None)

    return Releases(releases[0], releases[1])

def extract_rarities(card):
    '''Extract and return the rarities or None from the card JSON'''
    return tuple(sorted({cardset['set_rarity'] for cardset in card['card_sets']})) \
           if 'card_sets' in card else None

def extract_prices(card):
    '''Extract and return the prices from the card JSON'''
    prices = card['card_prices'][0]

    return Prices(float(prices['cardmarket_price']), float(prices['tcgplayer_price']))

def extract_sets(card):
    '''Extract and return the sets from the card JSON'''
    return tuple(
        Set(
            cset['set_code'],
            cset['set_name'],
            cset['set_rarity_code'],
            cset['set_rarity'],
            float(cset['set_price'].replace(',', ''))
        ) for cset in card['card_sets']
    ) if 'card_sets' in card else None

async def read(path):
    '''Read and return the contents of the file at the path'''
    with open(path, encoding='utf-8') as reader:
        return reader.read()

async def write(path, content):
    '''Write the content to the file at the path'''
    with open(path, 'w', encoding='utf-8') as writer:
        writer.write(content)

async def clean(client, revision):
    '''Clean the cache of outdated entries from the HTTP client and current revision'''
    for card in cards.values():
        card.rulings.clear()

    async with client.get(f'{YGORG}manifest/{revision}') as response:
        with suppress(KeyError, FileNotFoundError):
            for removable in (await response.json())['data']['qa']:
                remove(f'cache/{removable}')

async def cache(client, rid):
    '''Request and cache a ruling from its ID via the HTTP client'''
    async with client.get(f'{YGORG}data/qa/{rid}') as response:
        with open(f'cache/{rid}', 'w', encoding='utf-8') as entry:
            entry.write(dumps(await response.json()))

class Ruling:
    '''A representation of a ruling'''
    def __init__(self, ruling):
        '''Initialise a ruling from JSON'''
        self.rid = ruling['id']
        self.koids = set()
        self.question = self.replacekoids(ruling['question'])
        self.answer = self.replacekoids(ruling['answer'])
        self.date = ruling['thisSrc']['date']

    def replacekoids(self, text):
        '''Replace all KOIDs in the ruling text with card names and return the transformation'''
        for replaceable in findall('<<-?[0-9]*>>', text):
            koid = int(replaceable[2 : -2])
            text = text.replace(replaceable, koids[koid])
            self.koids.add(koid)

        return text

    async def make_embed(self):
        '''Make and return an embed of the ruling'''
        embed = Embed(
            colour=Colour.purple(),
            description=f'**{self.question}**\n\n>>> {self.answer}'
        )
        embed.set_author(
            icon_url=icons.QUESTION,
            name='Ruling',
            url=f'{YGORG}qa#{self.rid}'
        )
        embed.set_thumbnail(url=icons.RULING)
        embed.add_field(name='Involving', value=', '.join(koids[koid] for koid in self.koids))
        embed.set_footer(
            icon_url=icons.LOGO,
            text=f"{self.rid}{' • Speed Duel' if self.rid < 0 else ''} • {self.date}"
        )

        return embed

class Card: # pylint: disable=too-many-instance-attributes
    '''Representation of a card'''
    def __init__(self, card):
        self.name = card['name']
        self.ids = tuple(sorted(image['id'] for image in card['card_images']))
        self.koid = extract_koid(card)

        self.type = card['type']
        self.subtype = card['race']
        self.icon = icons.magic[self.type] if self.type in icons.magic \
                                           else icons.attributes[card['attribute']]

        self.levels = Levels(
            card['level'] if 'level' in card else None,
            card['scale'] if 'scale' in card else None,
            card['linkval'] if 'linkval' in card else None
        )
        if self.levels.link:
            self.arrows = card['linkmarkers']

        self.stats = extract_stats(card)
        self.text = self.extract_text(card['desc'])
        self.archetype = card['archetype'] if 'archetype' in card else None
        self.limits = self.extract_limits(card)
        self.releases = extract_releases(card)
        self.rarities = extract_rarities(card)
        self.prices = extract_prices(card)
        self.sets = extract_sets(card)
        self.rulings = []

    def extract_text(self, text):
        '''Extract and return the card text from the card text JSON'''
        if self.levels.scale:
            arrow = icons.arrows['Right']
            markers = Pendulum('Pendulum Effect', 'Monster Effect', 'Flavour Text')

            replacements = (
                ('\r\n', '\n'),
                ('-' * 40 + '\n', ''),
                ('Flavor', 'Flavour'),
                (f'[ {markers.pendulum} ]', f'{arrow} **{markers.pendulum}**\n'),
                (f'[ {markers.monster} ]', f'{arrow} **{markers.monster}**\n'),
                (f'[ {markers.flavour} ]', f'{arrow} **{markers.flavour}**\n'),
                ('\n\n', '\n')
            )

            for replacement in replacements:
                text = text.replace(*replacement)

            if 'Flavour Text' in text:
                replaceable = f'**{markers.flavour}**\n'

                text = text.replace(replaceable, f'{replaceable}*')
                text += '*'
            elif self.type == 'Pendulum Normal Monster':
                text = f'*{text}*'
        elif self.type.startswith('Normal'):
            text = f'*{text}*'

        text = f'**Card Text**\n>>> {text}'

        if self.levels.link:
            self.arrows.sort(key=lambda arrow : tuple(icons.arrows.keys()).index(arrow))

            arrows = []

            for arrow, icon in icons.arrows.items():
                if arrow in self.arrows:
                    arrows.append(icon)
                else:
                    arrows.append(icons.inactive_arrows[arrow])

            arrows.insert(4, icons.VOID)
            for i in (3, 7):
                arrows.insert(i, '\n')

            text = f"{''.join(arrows)}\n{text}"

        return text

    def extract_limits(self, card):
        '''Extract and return the limits from the card JSON'''
        limits = []

        if self.type != 'Skill Card':
            try:
                limits.append(card['banlist_info']['ban_tcg'])
            except KeyError:
                limits.append('Unlimited')

            try:
                limits.append(card['banlist_info']['ban_ocg'])
            except KeyError:
                limits.append('Unlimited')
        else:
            limits.extend([None] * 2)

        return Limits(limits[0], limits[1])

    async def formatlimits(self):
        '''Format and return the limits as a string'''
        with StringIO() as limits:
            if self.limits.tcg:
                limits.write(f'**TCG:** {self.limits.tcg} {icons.banlist[self.limits.tcg]}\n')
            if self.limits.ocg:
                limits.write(f'**OCG:** {self.limits.ocg} {icons.banlist[self.limits.ocg]}')

            return limits.getvalue().rstrip('\n')

    async def formatreleases(self):
        '''Format and return the release dates as a string'''
        with StringIO() as releases:
            if self.releases.tcg:
                releases.write(f'**TCG:** {self.releases.tcg}\n')
            if self.releases.ocg:
                releases.write(f'**OCG:** {self.releases.ocg}')

            return releases.getvalue().rstrip('\n')

    async def formatprices(self):
        '''Format and return the prices as a string'''
        cardmarket = f'https://www.cardmarket.com/en/YuGiOh/Cards/{quote(self.name)}'
        tcgplayer = f'https://www.tcgplayer.com/search/yugioh/product?q={quote(self.name)}'

        with StringIO() as prices:
            if self.prices.cardmarket:
                prices.write(f'**Cardmarket:** [€{self.prices.cardmarket:.2f}]({cardmarket})\n')
            if self.prices.tcgplayer:
                prices.write(f'**TCGplayer:** [${self.prices.tcgplayer:.2f}]({tcgplayer})')

            return prices.getvalue().rstrip('\n')

    async def formatids(self):
        '''Format and return the card IDs'''
        return ' • '.join(
            [str(cid).zfill(8) for cid in self.ids] + [str(self.koid)] if self.koid else []
        )

    async def make_title(self, subicon):
        '''Make and return the title section of the embed given the subtype icon'''
        with StringIO() as title:
            title.write(f'{subicon} {self.subtype} {self.type}\n')

            if self.levels.level:
                if not self.type.startswith('XYZ'):
                    title.write(f"{icons.level['level']} Level ")
                else:
                    title.write(f"{icons.level['rank']} Rank ")
                title.write(str(self.levels.level))

                if self.levels.scale is not None:
                    title.write(f"\n{icons.level['scale']} Scale {self.levels.scale}")
            elif self.levels.link:
                title.write(f"{icons.level['rating']} LINK-{self.levels.link}")
            title.write('\n')

            if self.stats.attack is not None:
                title.write(f'{icons.STATS} {self.stats.attack} ATK')
            if self.stats.defence is not None:
                title.write(f' / {self.stats.defence} DEF')

            return title.getvalue().rstrip('\n')

    async def make_embed(self):
        '''Make and return the embed'''
        colour = colours.types[self.type]
        url = f'{YGORG}card#{self.koid}' if self.koid else Embed.Empty
        image = ART.substitute(cid=min(self.ids))
        subicon = icons.subtypes[self.subtype] if self.subtype in icons.subtypes \
                                                               else icons.SKILLCHARACTER

        embed = Embed(colour=colour, title=await self.make_title(subicon), description=self.text)
        embed.set_author(icon_url=self.icon, name=self.name, url=url)
        embed.set_thumbnail(url=image)

        if self.archetype:
            embed.add_field(name='Archetype', value=self.archetype)
        if any(self.limits):
            embed.add_field(name='F&L Status', value=await self.formatlimits())
        if self.releases.tcg or self.releases.ocg:
            embed.add_field(name='Release', value=await self.formatreleases())
        if self.prices.cardmarket or self.prices.tcgplayer:
            embed.add_field(name='Price', value=await self.formatprices())
        if self.rarities:
            embed.add_field(name='Rarity', value=', '.join(self.rarities))

        embed.set_footer(icon_url=icons.LOGO, text=await self.formatids())

        return embed

    async def make_art_embed(self, cid):
        '''Make and return an art embed from a Card ID'''
        embed = Embed(colour=Colour.brand_red())
        embed.set_image(url=ART.substitute(cid=cid))
        embed.set_footer(icon_url=icons.LOGO, text=f'{self.name} • {str(cid).zfill(8)}')

        return embed

    async def make_art_embeds(self):
        '''Make and return art embeds'''
        return [await self.make_art_embed(cid) for cid in self.ids]

    async def make_set_embeds(self):
        '''Make and return set embeds or None'''
        if self.sets:
            grouplen = 5
            groups = (self.sets[i : i + grouplen] for i in range(0, len(self.sets), grouplen))

            embeds = []

            for group in groups:
                with StringIO() as description:
                    for cset in group:
                        description.write(
                            f'> **{cset.name}**\n'
                            f'> {cset.id}\n'
                            f'> *{cset.rarity} {cset.rarityid}*\n'
                        )
                        description.write(
                            f'> [${cset.price:.2f}]'
                            f'({ygoprices.substitute(set=quote(cset.name))})\n\n'
                            if cset.price else '\n'
                        )

                    embed = Embed(
                        colour=Colour.brand_green(),
                        description=description.getvalue().rstrip('\n')
                    )
                    embed.set_author(icon_url=icons.CARDS, name='Sets')
                    embed.set_thumbnail(url=icons.BOX)
                    embed.set_footer(icon_url=icons.LOGO, text=self.name)

                    embeds.append(embed)

            return embeds

    async def make_setimage_embed(self, name):
        '''Make and return a set embed given its name'''
        embed = Embed(colour=Colour.brand_green())
        embed.set_author(icon_url=icons.CARDS, name=name, url=ygoprices.substitute(set=quote(name)))
        embed.set_image(url=f'{YGOPRICES}set_image/{quote(name)}')
        embed.set_footer(icon_url=icons.LOGO, text=self.name)

        return embed

    async def make_setimage_embeds(self):
        '''Make and return set image embeds or None'''
        if self.sets:
            return [
                await self.make_setimage_embed(cset)
                for cset in sorted({cset.name for cset in self.sets})
            ]

    async def make_who_embed(self, seconds=30):
        '''Make and return a question embed, giving X seconds to answer'''
        timestamp = format_dt(datetime.now() + timedelta(seconds=seconds), style='T')

        embed = Embed(
            colour=Colour.nitro_pink(),
            description=f'You have {seconds} seconds to answer ({timestamp})'
        )
        embed.set_author(icon_url=icons.QUESTION, name='What card is this?')
        embed.set_image(url=ART.substitute(cid=self.ids[0]))

        return embed

    async def loadruling(self, rid):
        '''Load a ruling via its ID from the cache into a list'''
        ruling = loads(await read(f'cache/{rid}'))

        if 'en' in ruling['qaData']:
            self.rulings.append(Ruling(ruling['qaData']['en']))

    async def setrulings(self):
        '''Request and set the rulings'''
        async with aiohttp.ClientSession(raise_for_status=True) as client:
            with suppress(
                aiohttp.ClientConnectionError, aiohttp.ClientResponseError, asyncio.TimeoutError
            ):
                async with client.get(f'{YGORG}data/card/{self.koid}') as response:
                    rev = 'cache/revision'

                    if not exists(rev):
                        await write(rev, '0')

                    revision = await read(rev)
                    newrevision = response.headers['x-cache-revision']

                    if revision < newrevision:
                        await clean(client, revision)
                        await write(rev, newrevision)

                    for rid in (await response.json())['qaIndex']:
                        if not exists(f'cache/{rid}'):
                            await cache(client, rid)

                        await self.loadruling(rid)

    async def getrulings(self, keywords, index):
        '''Retrieve and return the rulings sorted by keyword matches or index'''
        if not self.rulings:
            await self.setrulings()

        return [
            await ruling.make_embed()
            for ruling in sorted(self.rulings,
                key=lambda ruling : sum(
                    keyword.lower() in tuple(word.lower() for word in ruling.question.split(' '))
                    for keyword in keywords.split(' ')
                ) if keywords else abs(ruling.rid - index),
                reverse=bool(keywords)
            )
        ]
