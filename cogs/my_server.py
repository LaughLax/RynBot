from discord.ext import commands
import asyncio


class MyServer:
    def __init__(self, bot):
        self.bot = bot

    def __local_check(self, ctx):
        return ctx.guild is not None and ctx.guild.id == 329681826618671104

    def _get_role_id(self, name: str):
        return {
            'LDSG': '357912587498946560'
        }.get(name)

    @commands.command(aliases=['iam', 'gibme', 'gimme'])
    async def giveme(self, ctx, *, i_want: str):
        """Self-assign user roles.

        Available roles are:
        LDSG"""
        id = self._get_role_id(i_want)
        if id is not None:
            conv = commands.RoleConverter()
            role = await conv.convert(ctx, id)
            if role in ctx.author.roles:
                await ctx.author.remove_roles(role)
            else:
                await ctx.author.add_roles(role)
            await ctx.message.add_reaction(u'\U0001F44D')
        else:
            await ctx.message.add_reaction(u'\U0001F44E')
        asyncio.sleep(3)
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(MyServer(bot))
