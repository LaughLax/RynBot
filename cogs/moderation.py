import typing

from discord import ChannelType
from discord import Embed
from discord import Member
from discord.ext.commands import Cog
from discord.ext.commands import bot_has_permissions
from discord.ext.commands import check
from discord.ext.commands import command
from discord.ext.commands import has_permissions


def mod_or_has_permissions(**perms):
    perm_check = has_permissions(**perms).predicate

    async def extended_check(ctx):
        if ctx.guild is None:
            return False

        mod_role_id = await ctx.bot.db.get_mod_role(ctx.guild.id)
        mod_role = ctx.guild.get_role(mod_role_id)
        is_mod = mod_role in ctx.author.roles

        return is_mod or await perm_check(ctx)

    return check(extended_check)


class Moderation(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command()
    @mod_or_has_permissions(manage_messages=True)
    @bot_has_permissions(manage_messages=True)
    async def purge(self, ctx, num: int = 10):
        """Purge up to 100 messages from a channel at once.

        Clears 10 messages by default."""
        await ctx.message.delete()
        if num > 100:
            num = 100
        await ctx.channel.purge(limit=num)

    @command()
    @mod_or_has_permissions(manage_roles=True)
    @bot_has_permissions(manage_roles=True)
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
    @bot_has_permissions(manage_roles=True)
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
    @bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: Member, *, reason: str = None):
        """Kick a member from the server.

        A reason can be provided."""

        # TODO Note who issued the command in the reason
        await member.kick(reason=reason)
        await ctx.message.delete()

    @command()
    @mod_or_has_permissions(ban_members=True)
    @bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: Member, *, reason: str = None):
        """Ban a member from the server.

        A reason can be provided."""

        # TODO Note who issued the command in the reason
        await member.ban(reason=reason)
        await ctx.message.delete()

    @command(aliases=['nick', 'nickname'])
    @mod_or_has_permissions(manage_nicknames=True)
    @bot_has_permissions(manage_nicknames=True)
    async def rename(self, ctx, member: Member, *, new_nick: str = None):
        """Change a user's nickname."""

        # TODO Place a reason in the audit logs, note who issued the command
        if new_nick and len(new_nick) > 32:
            await ctx.send('That nickname is too long; nicknames must be 32 characters or less.')
        else:
            await member.edit(nick=new_nick)

    @command()
    @mod_or_has_permissions(manage_channels=True)
    async def channels(self, ctx, *, member: typing.Optional[Member] = None):
        """Display a list of channels a user can see.

        If your guild has channels you don't want people to know about,
        be careful using this command!"""
        guild = ctx.guild
        member = member or ctx.author

        em = Embed(title=f'Channels viewable by {member}', color=0xff0000)
        em.set_author(name=ctx.guild.me.display_name, icon_url=self.bot.user.avatar_url)
        em.set_thumbnail(url=member.avatar_url)

        channels = guild.by_category()
        for cat, channel_list in channels:
            viewable_channels = []
            if cat is None:
                cat_title = 'No Category'
            else:
                cat_title = cat.name
            for channel in channel_list:
                perms = channel.permissions_for(member)
                if not perms.view_channel:
                    continue

                add_ons = []
                if channel.type == ChannelType.text:
                    chan_name = f'#{channel.name}'
                    if not perms.send_messages:
                        add_ons.append('read only')
                    if not perms.read_message_history:
                        add_ons.append('no history')
                elif channel.type == ChannelType.voice:
                    chan_name = channel.name
                    add_ons.append('voice')
                    if perms.connect and not perms.speak:
                        add_ons.append('listen only')
                    elif not perms.connect:
                        add_ons.append('view only')
                else:
                    chan_name = None

                if chan_name is not None:
                    if add_ons:
                        viewable_channels.append(f'**{chan_name}** ({", ".join(add_ons)})')
                    else:
                        viewable_channels.append(f'**{chan_name}**')

            if viewable_channels:
                em.add_field(name=cat_title, value='\n'.join(viewable_channels), inline=False)

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Moderation(bot))
