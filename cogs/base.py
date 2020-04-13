import sys
from datetime import datetime

from discord import Embed, Member
from discord.errors import Forbidden
from discord.ext.commands import Cog, command, ExtensionAlreadyLoaded
from discord.ext.commands.errors import CommandInvokeError, CommandNotFound, MissingRequiredArgument

from util import config


class Base(Cog):
    """Basic-level commands"""

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):

        for extension in config.cogs_other:
            try:
                self.bot.load_extension(extension)
            except Exception as e:
                if type(e) is not ExtensionAlreadyLoaded:
                    log = self.bot.get_cog('Logs')
                    if log:
                        await log.log('Failed to load extension {}.'.format(extension))
                    else:
                        print('Failed to load extension {}. Additionally, could not fetch logger.'.format(extension))
                    print(e)

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            return

        # Add a reaction to show it failed, if allowed
        try:
            await ctx.message.add_reaction(u'\u274C')
        except Forbidden:
            pass

        if isinstance(error, MissingRequiredArgument):
            await ctx.send("Insufficient arguments. Use `_help [command]` for more info.")
            return

        if isinstance(error, Forbidden):
            return

        if isinstance(error, CommandInvokeError):
            if isinstance(error.original, Forbidden):
                return

        # If it's an unhandled error, print to console
        print(ctx.message.content, file=sys.stderr)

        raise error

    @command(hidden=True)
    async def test(self, ctx):
        await ctx.message.add_reaction('\U0001F44D')

    @command()
    async def now(self, ctx):
        """Display the current time in UTC."""
        await ctx.send(datetime.utcnow().strftime("%Y-%m-%d %H:%M (UTC)"))

    @command()
    async def ping(self, ctx):
        """Check the bot's ping time."""
        start = datetime.now()
        await (await self.bot.ws.ping())
        td = datetime.now() - start
        await ctx.send("Pong. Response time: {} ms".format(td.total_seconds() * 1000))

    @command()
    async def userinfo(self, ctx, name: str = None):
        """Get user info. Ex: _info @user

        Lifted from appu1232's self-bot."""
        if name is None:
            user = ctx.message.author
        else:
            try:
                user = ctx.message.mentions[0]
            except:
                user = ctx.guild.get_member_named(name)
            if not user:
                user = ctx.guild.get_member(name)
            if not user:
                await ctx.send('Could not find user.')
                return

        # Thanks to IgneelDxD for help on this
        if user.avatar_url[54:].startswith('a_'):
            avi = 'https://images.discordapp.net/avatars/' + user.avatar_url[35:-10]
        else:
            avi = user.avatar_url

        role = user.top_role.name
        if role == "@everyone":
            role = "N/A"
        voice_state = None if not user.voice else user.voice.channel
        em = Embed(timestamp=ctx.message.created_at, colour=0xff0000)
        em.add_field(name='User ID', value=user.id, inline=True)
        if isinstance(user, Member):
            em.add_field(name='Nick', value=user.nick, inline=True)
            em.add_field(name='Status', value=user.status, inline=True)
            em.add_field(name='In Voice', value=voice_state, inline=True)
            em.add_field(name='Game', value=user.activity.name if user.activity else None, inline=True)
            em.add_field(name='Highest Role', value=role, inline=True)
        em.add_field(name='Account Created', value=user.created_at.__format__('%A, %d. %B %Y @ %H:%M:%S'))
        em.add_field(name='Join Date', value=user.joined_at.__format__('%A, %d. %B %Y @ %H:%M:%S'))
        em.set_thumbnail(url=avi)
        em.set_author(name=user, icon_url='https://cdn.discordapp.com/avatars/185095270986547200/e3d2e0cbfe668125f3f4a20356095e16.png?size=1024')
        await ctx.send(embed=em)

        if ctx.me.permissions_in(ctx.channel).manage_messages:
            await ctx.message.delete()

    @command()
    async def owner(self, ctx, *, message: str = None):
        """Send a message to the bot owner. Images and Discord-based emoji will not be shown."""

        # TODO Replace 'owner' command with an info command that links to the support server
        
        if message is not None:
            # TODO catch emojis (will require checking ctx.message instead of taking args)
            recipient = await self.bot.fetch_user(config.owner_id)
            if message.count("`") % 2 == 1:
                message = message + "`"
            await recipient.send("{0}\n\n`This message was sent to you by {1.name}#{1.discriminator} ({1.id}). To send him a message, use the `_message` command.`".format(message, ctx.author))
        else:
            ctx.send("You didn't give me a message to send!")


def setup(bot):
    bot.add_cog(Base(bot))
