import discord
from discord.ext import commands
from util import misc

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# TODO Clean up imports


class ActivePoll:
    """Object to hold information on one active poll."""
    def __init__(self, start, creator_id, options):
        self.start_time = start
        # self.end_time = self.start_time + timedelta(minutes=duration)
        self.creator_id = creator_id

        self.options = options
        self.votes = dict()

    def add_vote(self, user_id, option_id):
        if user_id in self.votes:
            if option_id not in self.votes[user_id]:
                self.votes[user_id].append(option_id)
        else:
            self.votes[user_id] = []
            self.votes[user_id].append(option_id)

    def remove_vote(self, user_id, option_id):
        if user_id in self.votes and option_id in self.votes[user_id]:
            self.votes[user_id].remove(option_id)

    def count_votes(self):
        totals = [0 for li in self.options]
        for v in self.votes:
            for i in self.votes[v]:
                totals[i] = totals[i] + 1
        return totals


class Polls(commands.Cog):
    """Poll commands, for Ryn's server only"""

    # TODO Count votes when poll is closed, instead of on every reaction
    # TODO Make polls persistent on restart
    # TODO Create option for single-choice poll

    vote_emojis = {'\U00000031\U000020e3': 0,
                   '\U00000032\U000020e3': 1,
                   '\U00000033\U000020e3': 2,
                   '\U00000034\U000020e3': 3,
                   '\U00000035\U000020e3': 4,
                   '\U00000036\U000020e3': 5,
                   '\U00000037\U000020e3': 6,
                   '\U00000038\U000020e3': 7,
                   '\U00000039\U000020e3': 8,
                   '\U0001f51f': 9}

    control_emojis = {'\U000023f9': 'stop'}

    def __init__(self, bot):
        self.bot = bot
        self.active_polls = dict()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, pl):
        if pl.message_id not in self.active_polls:
            return
        
        this_poll = self.active_polls.get(pl.message_id)
        if str(pl.emoji.name) in self.vote_emojis and self.vote_emojis[str(pl.emoji.name)] < len(this_poll.options):
            this_poll.add_vote(pl.user_id, self.vote_emojis[pl.emoji.name])
            # self.reaction_action(self, "_vote", emoji, message_id, channel_id, user_id)
        elif str(pl.emoji) in self.control_emojis and this_poll.creator_id == pl.user_id:
            await self.control_poll(pl.emoji, pl.message_id, pl.channel_id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, pl):
        if pl.message_id not in self.active_polls:
            return
        
        this_poll = self.active_polls.get(pl.message_id)
        if str(pl.emoji.name) in self.vote_emojis and self.vote_emojis[str(pl.emoji.name)] < len(this_poll.options) and pl.user_id in this_poll.votes:
            this_poll.remove_vote(pl.user_id, self.vote_emojis[pl.emoji.name])
            # self.reaction_action(self, "_unvote", emoji, message_id, channel_id, user_id)

    async def control_poll(self, emoji, message_id, channel_id):
        if str(emoji.name) in self.control_emojis and self.control_emojis[str(emoji.name)] == "stop":
            await self.end_poll(channel_id, message_id)

    async def end_poll(self, channel_id, message_id):

        poll = self.active_polls.pop(message_id)
        channel = self.bot.get_channel(channel_id)
        message = await misc.get_message(channel, message_id)

        plt.clf()
        plt.bar(range(len(poll.options)), poll.count_votes(), tick_label=poll.options, width=1., edgecolor='k')
        # plt.xticks(rotation=90, size='xx-small')
        # plt.xlabel("Poll Option")
        plt.ylabel("# of Votes")
        plt.title("Poll results")
        try:
            plt.tight_layout()

            plt.savefig('/var/www/html/RynBot/poll_results_{}.png'.format(message_id), format='png')
            plt.close()

            embed = discord.Embed(description="Poll closed.")
            # if message.embeds:
                # data = message.embeds[0]
                # if data.type == 'image':
                    # embed.set_image(url=data.url)

            # if message.attachments:
                # file = message.attachments[0]
                # if file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                    # embed.set_image(url=file.url)
                # else:
                    # embed.add_field(name='Attachment', value='[{}]({})'.format(file.filename, file.url), inline=False)

            embed.set_image(url='http://laughlax.us.to/RynBot/poll_results_{}.png'.format(message_id))
            embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar_url_as(format='png'))
            # embed.timestamp = message.created_at
            embed.colour = 0xff0000

            # await channel.send(file=discord.File(fp=f.getbuffer(), filename="poll_results.png"))
            await message.edit(embed=embed)
        except ValueError:
            await message.edit("Something went wrong, probably with scaling.")

    @commands.command()
    async def poll(self, ctx, *, items : str = None):
        if not isinstance(ctx.channel, discord.TextChannel) or items is None:
            return

        split = [a.strip() for a in items.split("|")]
        if len(split) <= 1:
            await ctx.send("A poll must have at least 2 options!")
        else:
            embed = discord.Embed()

            flat_emojis = sorted(list(self.vote_emojis.keys()))[0:len(split)]
            flat_emojis.extend(list(self.control_emojis.keys()))

            options_text = "\n".join(["{}: {}".format(flat_emojis[i], split[i]) for i in range(len(split))])
            embed.add_field(name="React to vote!", value=options_text)

            embed.add_field(name="Creator controls:", value="\U000023f9: End poll", inline=False)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url_as(format='png'))
            embed.timestamp = ctx.message.created_at

            message = await ctx.send(embed=embed)

            for emo in flat_emojis:
                await message.add_reaction(emo)

            poll = ActivePoll(message.created_at, ctx.author.id, options=split)
            self.active_polls[message.id] = poll


def setup(bot):
    bot.add_cog(Polls(bot))
