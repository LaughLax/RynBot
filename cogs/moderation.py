from discord import Member
from discord.ext.commands import bot_has_permissions
from discord.ext.commands import check
from discord.ext.commands import Cog
from discord.ext.commands import command
from discord.ext.commands import has_permissions


def mod_or_has_permissions(**perms):
    perm_check = has_permissions(**perms).predicate
    bot_perm_check = bot_has_permissions(**perms).predicate

    async def extended_check(ctx):
        if ctx.guild is None:
            return False

        mod_role_id = await ctx.bot.db.get_mod_role(ctx.guild.id)
        mod_role = ctx.guild.get_role(mod_role_id)
        is_mod = mod_role in ctx.author.roles

        if not (is_mod or await perm_check(ctx)):
            return False

        return await bot_perm_check(ctx)

    return check(extended_check)


class Moderation(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command()
    @mod_or_has_permissions(manage_messages=True)
    async def purge(self, ctx, num: int = 10):
        """Purge up to 100 messages from a channel at once.

        Clears 10 messages by default."""
        await ctx.message.delete()
        if num > 100:
            num = 100
        await ctx.channel.purge(limit=num)

    @command()
    @mod_or_has_permissions(manage_roles=True)
    async def mute(self, ctx, member: Member, *, reason: str = None):
        """Apply a "muted" role to a user.

        The server must have a Muted role set, and that role must be below the bot's highest role."""

        r_id = await self.bot.db.get_mute_role(ctx.guild.id)
        if r_id:
            role = ctx.guild.get_role(r_id)
            if role:
                if ctx.guild.me.top_role > role:
                    # TODO Note who issued the command in the reason
                    await member.add_roles(role, reason=reason)
                    # TODO Move messages to the log channel
                    await ctx.send(f'Muted role applied to {member}.')
                else:
                    await ctx.send(f'I can\'t apply the {role} role.')
            else:
                await ctx.send('I have a Muted role set, but it appears to be invalid.')
        else:
            await ctx.send('I don\'t have a Muted role set for this server.')

        await ctx.message.delete()

    @command()
    @mod_or_has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: Member, *, reason: str = None):
        """Remove a "muted" role from a user.

        The server must have a Muted role set, and that role must be below the bot's highest role."""

        r_id = await self.bot.db.get_mute_role(ctx.guild.id)
        if r_id:
            role = ctx.guild.get_role(r_id)
            if role:
                if role in member.roles:
                    if ctx.guild.me.top_role > role:
                        # TODO Note who issued the command in the reason
                        await member.remove_roles(role)
                        # TODO Move messages to the log channel
                        await ctx.send(f'{member} has been un-muted.')
                    else:
                        await ctx.send(f'I can\'t remove the {role} role.')
                else:
                    await ctx.send(f'That user isn\'t muted.')
            else:
                await ctx.send('I have a Muted role set, but it appears to be invalid.')
        else:
            await ctx.send('I don\'t have a Muted role set for this server.')

        await ctx.message.delete()

    @command()
    @mod_or_has_permissions(kick_members=True)
    async def kick(self, ctx, member: Member, *, reason: str = None):
        """Kick a member from the server.

        A reason can be provided."""

        # TODO Note who issued the command in the reason
        await member.kick(reason=reason)
        await ctx.message.delete()

    @command()
    @mod_or_has_permissions(ban_members=True)
    async def ban(self, ctx, member: Member, *, reason: str = None):
        """Ban a member from the server.

        A reason can be provided."""

        # TODO Note who issued the command in the reason
        await member.ban(reason=reason)
        await ctx.message.delete()

    @command(aliases=['nick', 'nickname'])
    @mod_or_has_permissions(manage_nicknames=True)
    async def rename(self, ctx, member: Member, *, new_nick: str = None):
        """Change a user's nickname."""

        # TODO Place a reason in the audit logs, note who issued the command
        # TODO Crop new nickname to max length
        await member.edit(nick=new_nick)


def setup(bot):
    bot.add_cog(Moderation(bot))
