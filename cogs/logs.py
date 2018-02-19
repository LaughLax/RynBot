import discord
from discord.ext import commands
from util import misc


class Logs:
    """Functions and event listeners for logging"""
    def __init__(self, bot):
        self.bot = bot
        self.log_chan = None
        # self.log_file = TODO maybe make a log file on the RPi

    async def on_ready(self):
        await self.log("Ayy, I'm awake!")

        for extension in misc.base_extensions:
            if extension not in self.bot.extensions:
                await self.log("Oh no! {} is not loaded! Trying to load...".format(extension))
                try:
                    self.bot.load_extension(extension)
                except Exception as e:
                    print('Failed to load extension {}.'.format(extension))
                    print(e)

#    async def on_shard_ready(self, shard_id):
#        pass
#
#    async def on_resumed(self):
#        pass
#
#    async def on_error(self, event):
#        pass

#    async def on_command_error(self, ctx, error):
#        if (isinstance(error, commands.errors.CommandNotFound) or
#           isinstance(error, commands.errors.MissingRequiredArgument)):
#            return
#
#        self.log(ctx.message.content)

    async def on_message_delete(self, message):
        if message.guild.id == misc.ryn_server_id:
            content = '{} deleted message in {}'.format(message.author.mention, message.channel.mention)

            embed = misc.embedify_message(message)

            if self.log_chan is None:
                self.log_chan = self.bot.get_channel(misc.bot_log_id)
            if self.log_chan is not None:
                await self.log_chan.send(content, embed=embed)
            else:
                print("While trying to log a deleted message, could not reach the #logs channel.")
        pass

    async def on_member_join(self, member):
        if member.guild.id == misc.ryn_server_id:
            self.log("<@{}> joined!".format(member.id))

    async def on_member_remove(self, member):
        if member.guild.id == misc.ryn_server_id:
            self.log("<@{}> left.".format(member.id))

#    async def on_member_update(self, before, after):
#        pass

    async def on_guild_join(self, guild):
        await self.log("I'm in a new guild! \"{0.name}\" ({0.member_count} members), {0.id}".format(guild))

    async def on_guild_remove(self, guild):
        await self.log("I've left a guild. \"{0.name}\" ({0.member_count} members), {0.id}".format(guild))

#    async def on_group_join(self, channel, user):
#        if user.id == self.bot.id:
#            await self.log_chan.send("Interesting, I'm in a group chat... \"{0.name}\" ({0.member_count} members), {0.id}".format(channel))
#
#    async def on_group_remove(self, channel, user):
#        pass

    async def log(self, text):

        # Add any file-based logging here.
        print(text)

        if self.log_chan is None:
            self.log_chan = self.bot.get_channel(misc.bot_log_id)
        if self.log_chan is not None:
            await self.log_chan.send(text)
        else:
            print("While trying to log the above, could not reach the #logs channel.")

    async def ping_ryn(self):
        if self.log_chan is None:
            self.log_chan = self.bot.get_channel(misc.bot_log_id)
        if self.log_chan is not None:
            await self.log_chan.send("<@{}>".format(misc.ryn_id))


def setup(bot):
    bot.add_cog(Logs(bot))
