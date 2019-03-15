import discord
from discord.ext import commands
from util import config
from util import misc


class StarError(commands.CheckFailure):
    pass


class Stars(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def get_starboard_channel(self, user_id):
        if user_id == config.owner_id:
            return self.bot.get_channel(config.ryn_starboard_id)
        else:
            return self.bot.get_channel(config.pub_starboard_id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, pl):
        [emoji, user_id, channel_id, message_id] = [pl.emoji, pl.user_id, pl.channel_id, pl.message_id]
        if self.bot.user.id == user_id:
            if user_id == config.owner_id and channel_id != config.ryn_starboard_id:
                await self.reaction_action('_star', emoji, message_id, channel_id, user_id)
        elif channel_id != config.pub_starboard_id:
            await self.reaction_action('_star', emoji, message_id, channel_id, user_id)

    async def reaction_action(self, fmt, emoji, message_id, channel_id, user_id):
        if str(emoji) != '\N{WHITE MEDIUM STAR}':
            return

        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel) or (user_id != config.owner_id and channel.guild.id != config.ryn_server_id):
            return

        method = getattr(self, '{}_message'.format(fmt))

        try:
            await method(channel, message_id, user_id)
        except StarError:
            pass

    async def _star_message(self, channel, message_id, user_id):
        """Stars a message.
        Parameters
        ------------
        channel: :class:`TextChannel`
            The channel that the starred message belongs to.
        message_id: int
            The message ID of the message being starred.
        user_id: int
            The user ID of the user starring the message.
        """

        # guild_name = channel.guild.name
        starboard_channel = self.get_starboard_channel(user_id)

        msg = await misc.get_message(channel, message_id)

        if msg is None:
            raise StarError('\N{BLACK QUESTION MARK ORNAMENT} This message could not be found.')

        if (len(msg.content) == 0 and len(msg.attachments) == 0) or msg.type is not discord.MessageType.default:
            raise StarError('\N{NO ENTRY SIGN} This message cannot be starred.')

        # at this point, we either edit the message or we create a message
        # with our star info
        content, embed = self.get_emoji_message(msg)

        await starboard_channel.send(content, embed=embed)

    @staticmethod
    def get_emoji_message(message):
        emoji = '\N{WHITE MEDIUM STAR}'

        content = '{} {} {} ID: {}'.format(emoji, message.guild.name, message.channel.mention, message.id)

        embed = misc.embedify_message(message)
        return content, embed


def setup(bot):
    bot.add_cog(Stars(bot))
