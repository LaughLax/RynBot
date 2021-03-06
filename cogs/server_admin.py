import asyncio
import typing

from discord import AllowedMentions
from discord import Role
from discord import TextChannel
from discord.errors import Forbidden
from discord.ext.commands import Cog
from discord.ext.commands import bot_has_permissions
from discord.ext.commands import command
from discord.ext.commands import group
from discord.ext.commands import has_permissions

from util import config


class ServerAdmin(Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        perm_check = has_permissions(manage_guild=True).predicate
        return ctx.guild is not None and await perm_check(ctx)

    @group(name='set')
    async def cfg_set(self, ctx):
        """Set server configuration."""

        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @group(name='get')
    async def cfg_get(self, ctx):
        """View server configuration."""

        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @cfg_set.command(name='log_channel')
    async def set_log_channel(self, ctx, channel: TextChannel = None):
        if channel is not None:
            perms = channel.permissions_for(ctx.guild.me)
            if perms.send_messages and perms.attach_files:
                await self.bot.db.set_log_channel(ctx.guild.id, channel.id)
                await ctx.send(f'The log channel for this guild has been set to {channel.mention}.')
            else:
                await ctx.send(f'I don\'t have enough permissions in {channel.mention}. '
                               'I need "Send Messages" and "Attach Files."')
        else:
            await self.bot.db.set_log_channel(ctx.guild.id, channel)
            await ctx.send('The log channel for this guild has been unset.')

    @cfg_get.command(name='log_channel')
    async def get_log_channel(self, ctx):
        c_id = await self.bot.db.get_log_channel(ctx.guild.id)
        if c_id:
            channel = ctx.guild.get_channel(c_id)
            if channel:
                await ctx.send(f'The log channel for this guild is {channel.mention}.')
            else:
                await ctx.send('There is a log channel set, but it appears to be invalid.')
        else:
            await ctx.send('The log channel for this guild is not set.')

    @cfg_set.command(name='mod_role')
    async def set_mod_role(self, ctx, role: Role = None):
        if role is not None:
            # TODO Make this a proper mention (but not actual mention) when d.py 1.4 comes out
            await self.bot.db.set_mod_role(ctx.guild.id, role.id)
            await ctx.send(f'The moderator role for this guild has been set to {role}.')
        else:
            await self.bot.db.set_mod_role(ctx.guild.id, role)
            await ctx.send('The moderator role for this guild has been unset.')

    @cfg_get.command(name='mod_role')
    async def get_mod_role(self, ctx):
        r_id = await self.bot.db.get_mod_role(ctx.guild.id)
        if r_id:
            role = ctx.guild.get_role(r_id)
            if role:
                # TODO Make this a proper mention (but not actual mention) when d.py 1.4 comes out
                await ctx.send(f'The moderator role for this guild is {role}.')
            else:
                await ctx.send('There is a moderator role set, but it appears to be invalid.')
        else:
            await ctx.send('The moderator role for this guild is not set.')

    @cfg_set.command(name='mute_role')
    async def set_mute_role(self, ctx, role: Role = None):
        if role is not None:
            if ctx.guild.me.top_role > role:
                # TODO Make this a proper mention (but not actual mention) when d.py 1.4 comes out
                await self.bot.db.set_mute_role(ctx.guild.id, role.id)
                await ctx.send(f'The mute role for this guild has been set to {role}.')
            else:
                await ctx.send(f'The mute role must be lower than my highest role. '
                               'The moderator role for this guild has not been changed.')
        else:
            await self.bot.db.set_mute_role(ctx.guild.id, role)
            await ctx.send('The mute role for this guild has been unset.')

    @cfg_get.command(name='mute_role')
    async def get_mute_role(self, ctx):
        r_id = await self.bot.db.get_mute_role(ctx.guild.id)
        if r_id:
            role = ctx.guild.get_role(r_id)
            if role:
                # TODO Make this a proper mention (but not actual mention) when d.py 1.4 comes out
                await ctx.send(f'The mute role for this guild is {role}.')
            else:
                await ctx.send('There is a mute role set, but it appears to be invalid.')
        else:
            await ctx.send('The mute role for this guild is not set.')

    @cfg_set.command(name='nickname', aliases=['nick'])
    @bot_has_permissions(change_nickname=True)
    async def set_nickname(self, ctx, *, new_nick: str = None):
        """Set the bot's nickname in this guild."""

        if new_nick and len(new_nick) > 32:
            await ctx.send('That nickname is too long; nicknames must be 32 characters or less.')
        else:
            await ctx.me.edit(nick=new_nick)

    @cfg_set.command(name='prefix')
    async def set_prefix(self, ctx, *, prefix=None):
        await self.bot.db.set_prefix(ctx.guild.id, prefix)
        if prefix is not None:
            await ctx.send(f'The command prefix for this guild has been set to "{prefix}". '
                           'Mentioning me also works as a prefix.')
        else:
            await ctx.send('The command prefix for this guild has been reset to default '
                           f'(Mention or "{config.prefix}")')

    @cfg_get.command(name='prefix')
    async def get_prefix(self, ctx):
        pref = await self.bot.db.get_prefix(ctx.guild.id)
        pref = pref or config.prefix
        await ctx.send(f'The command prefix for this guild is "{pref}". '
                       'Mentioning me also works as a prefix.')

    @cfg_set.command(name='role')
    async def set_self_assign_role(self, ctx, role: typing.Optional[Role] = None, *, role_name: str):
        if role is not None:
            if ctx.me.top_role > role:
                await self.bot.db.set_self_assign_role(ctx.guild.id, role.id, role_name)
                await ctx.send(f'Self-assignable role "{role_name}" set to {role.mention}!',
                               allowed_mentions=AllowedMentions.none())
            else:
                await ctx.send('That role is higher than my highest; I can\'t give it or take it.')
        else:
            await self.bot.db.delete_self_assign_role(ctx.guild.id, role_name)
            await ctx.send(f'Self-assignable role "{role_name}" cleared!')

    @cfg_get.command(name='roles')
    async def get_self_assign_roles(self, ctx):
        roles = await self.bot.db.get_self_assign_roles(ctx.guild.id)
        await ctx.send('\n'.join([f'"{r[1]}": {ctx.guild.get_role(r[0]).mention}' for r in roles]),
                       allowed_mentions=AllowedMentions.none())

    @cfg_set.command(name='starboard')
    async def set_starboard(self, ctx, channel: TextChannel = None):
        if channel:
            perms = channel.permissions_for(ctx.guild.me)
            if perms.send_messages and perms.attach_files:
                await self.bot.db.set_starboard_channel(ctx.guild.id, channel.id)
                await ctx.send(f'This server\'s starboard has been set to {channel.mention}.')
            else:
                await ctx.send('I don\'t have enough permissions in that channel. '
                               'I need "Send Messages" and "Attach Files."')
        else:
            await self.bot.db.set_starboard_channel(ctx.guild.id, channel)
            await ctx.send(f'This server\'s starboard has been disabled.')

    @cfg_get.command(name='starboard')
    async def get_starboard(self, ctx):
        star_channel = await self.bot.db.get_starboard_channel(ctx.guild.id)
        star_channel = self.bot.get_channel(star_channel)

        if star_channel:
            await ctx.send(f'This server\'s starboard is {star_channel.mention}.')
        else:
            await ctx.send('This server has no assigned starboard.')

    @cfg_set.command(name='star_threshold', aliases=['min_stars'])
    async def set_star_threshold(self, ctx, min_stars: int = 1):
        if min_stars > 0:
            await self.bot.db.set_star_threshold(ctx.guild.id, min_stars)
            await ctx.send(f'The number of stars needed to reach the starboard has been set to {min_stars}.')
        else:
            await ctx.send('The star threshold must be a positive integer.')

    @cfg_get.command(name='star_threshold', aliases=['min_stars'])
    async def get_star_threshold(self, ctx):
        min_stars = await self.bot.db.get_star_threshold(ctx.guild.id)
        await ctx.send(f'A message needs {min_stars} star{"s" if min_stars > 1 else ""} to reach the starboard.')

    @command()
    async def leave(self, ctx):
        """Ask the bot to leave the server."""

        confirm_msg = await ctx.send('Are you sure you want me to leave the server? '
                                     'React with ??? within 60 seconds to confirm. '
                                     'React with ??? to cancel.')
        try:
            await confirm_msg.add_reaction('???')
            await confirm_msg.add_reaction('???')
        except Forbidden:
            pass

        def check(r, u):
            return u == ctx.author \
                   and str(r.emoji) in ['???', '???'] \
                   and r.message.id == confirm_msg.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
            if str(reaction.emoji) == '???':
                await confirm_msg.edit(content='Request to leave server confirmed. Leaving...')
                await ctx.guild.leave()
            else:
                await confirm_msg.edit(content='Request to leave server cancelled.')
        except asyncio.TimeoutError:
            await confirm_msg.edit(content='Request to leave server timed out.')


def setup(bot):
    bot.add_cog(ServerAdmin(bot))
