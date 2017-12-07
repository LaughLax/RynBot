import discord
from discord.ext import commands
from datetime import datetime
import sys


class Base:
    def __init__(self, bot):
        self.bot = bot

    async def on_command_error(self, ctx, error):
        await ctx.message.add_reaction(u'\u274C')
        print(ctx.message.content, file=sys.stderr)
        raise error

    @commands.command()
    async def test(self, ctx):
        await ctx.message.add_reaction('\U0001F44D')

    @commands.command()
    async def now(self, ctx):
        await ctx.send(datetime.utcnow().strftime("%Y-%m-%d %H:%M (UTC)"))

    @commands.command()
    async def ping(self, ctx):
        start = datetime.now()
        await (await self.bot.ws.ping())
        td = datetime.now() - start
        await ctx.send("Pong. Response time: {} ms".format(td.total_seconds() * 1000))

    @commands.command()
    async def userinfo(self, ctx, name: str = None):
        """Get user info. Ex: >info @user

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
        em = discord.Embed(timestamp=ctx.message.created_at, colour=0xff0000)
        em.add_field(name='User ID', value=user.id, inline=True)
        em.add_field(name='Nick', value=user.nick, inline=True)
        em.add_field(name='Status', value=user.status, inline=True)
        em.add_field(name='In Voice', value=voice_state, inline=True)
        em.add_field(name='Game', value=user.game, inline=True)
        em.add_field(name='Highest Role', value=role, inline=True)
        em.add_field(name='Account Created', value=user.created_at.__format__('%A, %d. %B %Y @ %H:%M:%S'))
        em.add_field(name='Join Date', value=user.joined_at.__format__('%A, %d. %B %Y @ %H:%M:%S'))
        em.set_thumbnail(url=avi)
        em.set_author(name=user, icon_url='https://i.imgur.com/RHagTDg.png')
        await ctx.send(embed=em)

        if ctx.me.permissions_in(ctx.channel).manage_messages:
            await ctx.message.delete()


def setup(bot):
    bot.add_cog(Base(bot))
