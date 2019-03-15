import discord
from discord.ext import commands
from util import config


class Logs(commands.Cog):
    """Functions and event listeners for logging"""
    def __init__(self, bot):
        self.bot = bot
        self.log_chan = None
        # self.log_file = TODO maybe make a log file on the RPi

    @commands.Cog.listener()
    async def on_ready(self):
        await self.log("Ayy, I'm awake!")

        for extension in config.cogs_core:
            if extension not in self.bot.extensions:
                await self.log("Oh no! {} is not loaded! Trying to load...".format(extension))
                try:
                    self.bot.load_extension(extension)
                except Exception as e:
                    await self.log('Failed to load extension {}.\n{}'.format(extension, e))

#    @commands.Cog.listener()
#    async def on_shard_ready(self, shard_id):
#        pass
#
#    @commands.Cog.listener()
#    async def on_resumed(self):
#        pass
#
#    @commands.Cog.listener()
#    async def on_error(self, event):
#        pass

#    @commands.Cog.listener()
#    async def on_command_error(self, ctx, error):
#        if (isinstance(error, commands.errors.CommandNotFound) or
#           isinstance(error, commands.errors.MissingRequiredArgument)):
#            return
#
#        await self.log(ctx.message.content)

    '''
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild.id == misc.ryn_server_id:
            content = 'Message by {} deleted in {}'.format(message.author.mention, message.channel.mention)

            embed = misc.embedify_message(message)

            if self.log_chan is None:
                self.log_chan = self.bot.get_channel(misc.bot_log_id)
            if self.log_chan is not None:
                await self.log_chan.send(content, embed=embed)
            else:
                print("While trying to log a deleted message, could not reach the #logs channel.")
        pass
    '''

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == config.ryn_server_id:
            await self.log("{0.name}#{0.discriminator} (<@{0.id}>, nick `{0.nick}`) joined.".format(member))

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id == config.ryn_server_id:
            await self.log("{0.name}#{0.discriminator} (<@{0.id}>, nick `{0.nick}`) left.".format(member))

#    async def on_member_update(self, before, after):
#        pass

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.log("I'm in a new guild! \"{0.name}\" ({0.member_count} members), {0.id}".format(guild))

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.log("I've left a guild. \"{0.name}\" ({0.member_count} members), {0.id}".format(guild))

#    @commands.Cog.listener()
#    async def on_group_join(self, channel, user):
#        if user.id == self.bot.id:
#            await self.log_chan.send("Interesting, I'm in a group chat... \"{0.name}\" ({0.member_count} members), {0.id}".format(channel))
#
#    @commands.Cog.listener()
#    async def on_group_remove(self, channel, user):
#        pass

    async def log(self, text):

        # Add any file-based logging here.
        print(text)

        if self.log_chan is None:
            self.log_chan = self.bot.get_channel(config.bot_log_id)
        if self.log_chan is not None:
            await self.log_chan.send(text)
        else:
            print("While trying to log the above, could not reach the #logs channel.")

    async def ping_ryn(self):
        if self.log_chan is None:
            self.log_chan = self.bot.get_channel(config.bot_log_id)
        if self.log_chan is not None:
            await self.log_chan.send("<@{}>".format(config.owner_id))


def setup(bot):
    bot.add_cog(Logs(bot))
