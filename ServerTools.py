import discord
from discord.ext import commands
import re
from utils import checks
import dice
import io
import random


class ServerTools:
    def __init__(self, bot):
        self.bot = bot
        self.channel_regex = re.compile(r'@#((?:\w\s?){1,30})', re.IGNORECASE)

    async def on_message(self, message):
        search = re.search(self.channel_regex, message.content)
        if search is not None:
            search_word = search.group(1).lower()
            channel = next(x for x in message.server.channels if search_word in x.name.lower())
            if channel is not None:
                if channel.type is discord.ChannelType.voice:
                    await self.bot.send_message(message.channel,
                                                ', '.join([x.mention for x in channel.voice_members[:6]]))

    @commands.command(pass_context=True)
    @commands.cooldown(1, 220, type=commands.BucketType.server)
    async def archive(self, ctx, count: int = 100):
        file = io.BytesIO()
        log_list = []
        if count > 10000:
            count = 10000
        async for msg in self.bot.logs_from(ctx.message.channel, limit=count):
            log_list.append('[{}] <{}>: {}'.format(msg.timestamp.strftime('%F %H:%M'), msg.author.display_name,
                                                   msg.clean_content))
            if msg.embeds:
                for embed in msg.embeds:
                    log_list.append('Embed:')
                    for key, value in embed.items():
                        log_list.append('{} : {}'.format(key, value))
            if msg.attachments:
                try:
                    msg.attachments[0]['height']
                    log_list.append('with image {} '.format(msg.attachments[0]['filename']))
                except KeyError:
                    log_list.append('with file {} '.format(msg.attachments[0]['filename']))

        log_list.reverse()
        file.write(bytes('\r\n'.join(log_list), 'utf-8'))
        file.seek(0)
        await self.bot.send_file(ctx.message.channel, file, filename='logs.txt', content='Archived {} messages'
                                 .format(count))

    @commands.command(pass_context=True)
    @checks.is_botbanned()
    async def quote(self, cxt, quoteid, lim=500):
        """Quotes a message! Usage: &quote <message ID>"""
        async for msg in self.bot.logs_from(cxt.message.channel, limit=lim):
            if msg.id == quoteid:
                quote = msg
                break
        regex = re.compile('(?P<url>https?://[^\s]+(jpg|png))')
        em = discord.Embed(description=quote.content, colour=0x789922, timestamp=quote.timestamp)
        if re.match(regex, quote.content) is not None:
            em.set_image(re.match(regex, quote.content))
        em.set_author(name=quote.author.name, icon_url=quote.author.avatar_url)
        await self.bot.say(embed=em)

    @commands.command()
    @checks.is_botbanned()
    async def searchusers(self, name):
        """Usage: &searchusers <username>. Returns the origin profile search page for that username."""
        await self.bot.say('https://www.origin.com/usa/en-us/search?searchString={}&category=people'.format(name))

    @commands.command()
    @checks.is_botbanned()
    @commands.cooldown(1, 30, type=commands.BucketType.user)
    async def roll(self, *, dice_string):
        """Rolls XdY dice.
Advanced functions:
Supports basic arithmetic (1d6 + 5)
Selecting the n lowest/highest roles can be done with ^ and v, (6d6^3) uses only the 3 highest rolls
You can also add different dice (2d8 + 1d20)"""
        if len(dice_string) < 100:
            dice_roll = dice.roll(dice_string)
            try:
                dice_sum_string = str(sum(dice_roll))
                if len(dice_sum_string) > 10:
                    dice_sum_string = '{:.10e}'.format(sum(dice_roll))
            except TypeError:
                dice_sum_string = str(dice_roll)
                if len(dice_sum_string) > 10:
                    dice_sum_string = '{:.10e}'.format(dice_roll)

            dice_roll_string = 'Rolling **{}** \n =**{}**'.format(dice_string, dice_sum_string)
            await self.bot.say(dice_roll_string)
        else:
            await self.bot.say('Quit trying to fuck up the bot')

    @commands.command(pass_context=True)
    @checks.is_botbanned()
    async def whosplaying(self, ctx, *, game=None):
        """Tells you how many people are playing <game>
Not providing a game will give you the top 10 played games"""
        game_name = game
        if game_name == 'games' or game_name is None:
            game_dict = {}
            for m in ctx.message.server.members:
                if m.game is not None:
                    game_dict[m.game.name] = game_dict.get(m.game.name, 0) + 1
            sorted_dict = sorted(game_dict.items(), key=(lambda y: y[1]), reverse=True)
            say_string = 'Games being played: \n' + '\n'.join(
                ['**{}** people playing **{}**'.format(value, key) for (key, value) in sorted_dict][:10])
            await self.bot.say(say_string)

        else:
            game_list = []
            for x in ctx.message.server.members:
                if x.game is not None:
                    if game_name.lower() in x.game.name.lower():
                        game_list.append('**{}**'.format(x.display_name))
            await self.bot.say(
                'There are **{}** people playing **{}**:\n{}'.format(len(game_list), game_name, '\n'.join(game_list)))

    @commands.command(pass_context=True)
    async def admincheck(self, ctx, user_to_check: discord.Member):
        """Checks if someone has admin permissions. """
        sw = user_to_check
        total_perms = [sw.permissions_in(x) for x in ctx.message.server.channels]
        for p in total_perms:
            if p.administrator \
                    or p.ban_members or p.kick_members or p.manage_messages or p.manage_nicknames or p.manage_roles:
                await self.bot.say('{} has admin permissions!'.format(user_to_check.display_name))
                return
        await self.bot.say('{} does not have admin permissions.'.format(user_to_check.display_name))

    @commands.command(pass_context=True)
    async def loadout(self, ctx, *, kit=None):
        """Gives you a random Pilot or Titan Loadout. Usage: &loadout <pilot/titan>"""

        def random_if_not_in(string, random_list):
            if string is None:
                return random.choice(random_list)
            string = string.lower().replace(" ", "")
            return next((x for x in random_list if string in x.lower().replace(" ", "")), random.choice(random_list))

        def pilot(pilot_type):
            primary_list = ['G2A5', 'Hemlok BF-R', 'R201 Carbine', 'R101 Carbine', 'V47 Flatline',
                            'Alternator', 'CAR', 'R - 97 Compact SMG', 'Volt',
                            'L - STAR', 'Spitfire', 'X - 55 Devotion',
                            'D - 2 Double Take', 'Kraber AP', 'Longbow - DMR',
                            'EVA-8', 'Mastiff',
                            'EM - 4 Cold War', 'EPG - 1', 'R - 6P Softball', 'Sidewinder SMR']
            secondary_list = ['Wingman', 'Wingman Elite', 'P2016', 'RE-45 Auto', 'Mozambique',
                              'Archer', 'Charge Rifle', 'Thunderbolt', 'MGL']
            ordnance_list = ['Gravity Star', 'Satchel', 'Firestar', 'Frag Grenade', 'Arc Grenade', 'Electric Smoke']
            tactical_list = ['Grapple', 'HoloPilot', 'Pulse Blade', 'Stim', 'Cloak', 'Phase Shift', 'A-Wall']
            kit1_list = ['Phase Embark', 'Ordnance Expert', 'Fast Regen', 'Power Cell']
            kit2_list = ['Kill Report', 'Wall Hang', 'Hover', 'Low Profile']
            boost_list = ['Amped Weapons', 'Ticks', 'Smart Pistol', 'Map Hack', 'Pilot Sentry', 'Battery Back-up',
                          'Radar Jammer', 'Titan Sentry', 'Phase Rewind', 'Hard Cover', 'Holo Pilot Nova',
                          'DiceRoll']
            primary = random_if_not_in(pilot_type, primary_list)
            secondary = random_if_not_in(pilot_type, secondary_list)
            ordnance = random_if_not_in(pilot_type, ordnance_list)
            tactical = random_if_not_in(pilot_type, tactical_list)
            kit1 = random_if_not_in(pilot_type, kit1_list)
            kit2 = random_if_not_in(pilot_type, kit2_list)
            boost = random_if_not_in(pilot_type, boost_list)
            return """**Primary: **{}
**Secondary: **{}
**Tactical: **{}
**Ordinance: **{}
**Kit 1: **{}
**Kit 2: **{}
**Boost: **{}""".format(primary, secondary, tactical, ordnance, kit1, kit2, boost)

        def titan(titan_type):
            titan_list = ['Tone', 'Scorch', 'Ronin', 'Ion', 'Legion', 'Northstar', 'Monarch']
            titan_kit1_list = ['Assault Chip', 'Stealth Auto-Eject', 'Turbo Engine', 'Overcore', 'Nuclear Ejection',
                               'Counter Ready']
            titan_name = random_if_not_in(titan_type, titan_list)
            kit1 = random_if_not_in(titan_type, titan_kit1_list)
            if titan_name == 'Tone':
                kit2 = random.choice(['Enhanced Tracker Rounds', 'Reinforced Particle Wall', 'Pulse-Echo',
                                      'Rocket Barrage', 'Burst Loader'])
            elif titan_name == 'Scorch':
                kit2 = random.choice(['Wildfire Launcher', 'Tempered Plating', 'Inferno Shield', 'Fuel for the Fire',
                                      'Scorched Earth'])
            elif titan_name == 'Ronin':
                kit2 = random.choice(
                    ['Ricochet Rounds', 'Thunderstorm', 'Temporal Anomaly', 'Highlander', 'Phase Reflex'])
            elif titan_name == 'Ion':
                kit2 = random.choice(['Entangled Energy', 'Zero-Point Trip Wire', 'Vortex Amplifier', 'Grand Cannon',
                                      '5-Way Splitter'])
            elif titan_name == 'Legion':
                kit2 = random.choice(['Enhanced Ammo Capacity', 'Sensor Array', 'Bulwark', 'Light-Weight Alloys',
                                      'Hidden Compartment'])
            elif titan_name == 'Northstar':
                kit2 = random.choice(['Piercing Shot', 'Enhanced Payload', 'Twin Traps', 'Viper Thrusters',
                                      'Threat Optics'])
            elif titan_name == 'Monarch':
                kit2 = random.choice(['Shield Amplifier', 'Energy Theif', 'Survival of the Fittest', 'Rapid Rearm'])
                kit2 += '\n**Core upgrades:** {}, {}, {}'.format(
                    random.choice(['Arc rounds', 'Missile Racks', 'Energy Transfer']),
                    random.choice(['Rearm and Reload', 'Maelstrom', 'Energy Field']),
                    random.choice(['Multi-Target Missiles', 'Superior Chassis', 'XO-16 Accelerator'])
                )
            else:
                kit2 = 'something strange'
            fallkit = random.choice(['Warpfall', 'Bubbleshield'])
            return """**Titan:**{}
**Kit 1: **{}
**Kit 2: **{}
**Titanfall Kit: **{}""".format(titan_name, kit1, kit2, fallkit)

        if kit == 'pilot':
            msg = pilot(kit)
        elif kit == 'titan':
            msg = titan(kit)
        else:
            msg = '{}\n{}'.format(pilot(kit), titan(kit))
        await self.bot.say(msg)

    @commands.command(name='6roll')
    async def six_roll(self, count: int = 1):
        rolls = [random.randint(1, 6) for _ in range(0, count)]
        hits = sum(1 for x in rolls if x >= 5)
        message = 'Rolled {}D6, {} hits: {}'.format(str(count), str(hits), ', '.join(
            [str(x) if x < 5 else '**{}**'.format(str(x)) for x in rolls]))
        if rolls.count(1) >= count / 2:
            if hits == 0:
                message += '\n**Critical glitch!**'
            else:
                message += '\nGlitch!'
        await self.bot.say(message)


def setup(bot):
    bot.add_cog(ServerTools(bot))
