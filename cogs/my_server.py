from discord.ext.commands import Cog, command, RoleConverter

from util import config


class MyServer(Cog):
    """Commands exclusively for Ryn's server"""
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        return ctx.guild is not None and ctx.guild.id == config.ryn_server_id

    def _get_role_id(self, name: str):
        return {
            'ldsg': '357912587498946560'
        }.get(name.lower())

    @command(aliases=['iam', 'gibme', 'gimme'])
    async def giveme(self, ctx, *, i_want: str):
        """Self-assign user roles.

        Available roles are:
        LDSG"""
        id = self._get_role_id(i_want)
        if id is not None:
            conv = RoleConverter()
            role = await conv.convert(ctx, id)
            if role in ctx.author.roles:
                await ctx.author.remove_roles(role)
            else:
                await ctx.author.add_roles(role)
            await ctx.message.add_reaction(u'\U0001F44D')   # :thumbsup:
        else:
            await ctx.message.add_reaction(u'\U0001F44E')   # :x:

    @command(aliases=['civil'])
    async def burnitdown(self, ctx):
        msg = await ctx.send('''Wow great discussion
*locks channel*
Very civil
*bans everyone*
Lots of fun
*burns server to the ground*''')
        await msg.add_reaction('\U0001F525')    # :fire:


def setup(bot):
    bot.add_cog(MyServer(bot))
