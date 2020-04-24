import typing

from discord import ActivityType, Embed, Member, Role, TextChannel
from discord.ext.commands import bot_has_permissions, Cog, command, group, guild_only, has_permissions

from util import config


class Server(Cog):
    def __init__(self, bot):
        self.bot = bot

    @group(name='set')
    @guild_only()
    @has_permissions(manage_guild=True)
    async def cfg_set(self, ctx):
        pass

    @group(name='get')
    @guild_only()
    @has_permissions(manage_guild=True)
    async def cfg_get(self, ctx):
        pass

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
        pref = config.prefix if pref is None else pref
        await ctx.send(f'The command prefix for this guild is "{pref}". '
                       'Mentioning me also works as a prefix.')

    @cfg_set.command(name='mute_role')
    async def set_mute_role(self, ctx, role: Role = None):
        if role is not None:
            # TODO Make this a proper mention (but not actual mention) when d.py 1.4 comes out
            await self.bot.db.set_mute_role(ctx.guild.id, role.id)
            await ctx.send(f'The mute role for this guild has been set to {role}.')
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

    @cfg_set.command(name='starboard')
    async def set_starboard(self, ctx, channel: typing.Optional[TextChannel] = None):
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
    @has_permissions(manage_messages=True)
    @bot_has_permissions(manage_messages=True)
    async def purge(self, ctx, num: int = 10):
        """Purge up to 100 messages from a channel at once.

        Clears 10 messages by default."""
        await ctx.message.delete()
        if num > 100:
            num = 100
        await ctx.channel.purge(limit=num)

    @command()
    @has_permissions(kick_members=True)
    @bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: Member, reason: str = None):
        """Kick a member from the server.
        
        A reason can be provided."""

        # TODO Note who issued the command in the reason
        await member.kick(reason=reason)
        await ctx.message.delete()

    @command()
    @has_permissions(ban_members=True)
    @bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: Member, reason: str = None):
        """Ban a member from the server.

        A reason can be provided."""

        # TODO Note who issued the command in the reason
        await member.ban(reason=reason)
        await ctx.message.delete()

    @command(aliases=['nick', 'nickname'])
    @has_permissions(manage_nicknames=True)
    @bot_has_permissions(manage_nicknames=True)
    async def rename(self, ctx, member: Member, new_nick: str = None):
        """Change a user's nickname."""

        # TODO Place a reason in the audit logs, note who issued the command
        await member.edit(nick=new_nick)

    @command(aliases=['whoisplaying'])
    async def nowplaying(self, ctx, *, game_title: str):
        """List users playing a specific game."""
        if game_title is not None:
            users = []
            for a in ctx.guild.members:
                if a.activity is not None and a.activity.type == ActivityType.playing and a.activity.name is not None:
                    if a.activity.name.lower() == game_title.lower():
                        users.append(a.name)
            if len(users) == 0:
                await ctx.send("No users found playing {}.".format(game_title))
            else:
                title = "Server: {}".format(ctx.guild.name)
                header = "Game: {}".format(game_title)

                users.sort()
                body = "\n".join(users)

                em = Embed(title=title, color=0xff0000, timestamp=ctx.message.created_at)
                em.add_field(name=header, value=body)

                await ctx.send(embed=em)
                if ctx.me.permissions_in(ctx.channel).manage_messages:
                    await ctx.message.delete()
        else:
            await ctx.send("No game specified.")

    @command()
    @has_permissions(manage_channels=True)
    async def channels(self, ctx):
        """Display a list of all channels on the server to use.

        This command requires the "Manage Channels" permission.
        If your server has channels you don't want people to know about,
        be careful using this command!"""
        server = ctx.guild

        title = str.format("Server: {0.name} (ID {0.id})", server)

        chans = server.channels
        text_avail = []
        text_hidden = []
        for a in chans:
            if type(a) is TextChannel:
                if a.permissions_for(server.me).read_messages:
                    text_avail.append(a.name)
                else:
                    text_hidden.append(a.name)

        text_avail.sort()
        text_hidden.sort()

        display_size = 40
        num_segments = int(max(len(text_avail)/display_size, len(text_hidden)/display_size)) + 1

        for b in range(num_segments):
            start = b*display_size
            end = (b+1)*display_size - 1
            em = Embed(title=title, color=0xff0000, timestamp=ctx.message.created_at)

            if text_avail[start:end]:
                text_avail_body = "\n".join(text_avail[start:end])
                em.add_field(name='Unhidden text channels', value=text_avail_body)

            if text_hidden[start:end]:
                text_hidden_body = "\n".join(text_hidden[start:end])
                em.add_field(name='Hidden text channels', value=text_hidden_body)

            icon_url = server.icon_url
            em.set_thumbnail(url=icon_url)

            footer = "Page {}/{}".format(b+1, num_segments)
            em.set_footer(text=footer)

            await ctx.send(embed=em)

        if ctx.me.permissions_in(ctx.channel).manage_messages:
            await ctx.message.delete()

    @command()
    @has_permissions(manage_roles=True)
    async def roles(self, ctx):
        """Display a list of all roles on the server.

        This command requires the "Manage Roles" permission to use.
        If your server has channels you don't want people to know about,
        be careful using this command!"""
        server = ctx.guild

        title = "Server: {0.name} (ID {0.id})".format(server)

        role_list = []
        for a in server.roles:
            if not a.is_default():
                role_list.append(a.name)
        role_list.reverse()

        display_size = 60
        num_segments = int(len(role_list)/display_size) + 1
        for b in range(num_segments):
            embed = Embed(title=title, color=0xff0000, timestamp=ctx.message.created_at)
            embed.set_thumbnail(url=server.icon_url)

            embed.add_field(name='Roles', value=', '.join(role_list[b*display_size:(b+1)*display_size-1]))

            footer = "Page {}/{}".format(b+1, num_segments)
            embed.set_footer(text=footer)

            await ctx.send(embed=embed)

        if ctx.me.permissions_in(ctx.channel).manage_messages:
            await ctx.message.delete()

    @command()
    async def nowstreaming(self, ctx):
        """Display a list of all users streaming on the server."""
        streamers = []
        for a in ctx.guild.members:
            if a.activity is not None and a.activity.type == ActivityType.streaming:
                streamers.append(a)

        streamers.sort(key=lambda mem: mem.display_name)

        if len(streamers) > 0:
            display_size = 20
            num_segments = int(len(streamers)/display_size) + 1
            if num_segments <= 5:
                for b in range(num_segments):
                    em = Embed(title='Guild Members Streaming', color=0xff0000, timestamp=ctx.message.created_at)
                    em.set_thumbnail(url=ctx.guild.icon_url)
                    for a in streamers[b*display_size:(b+1)*display_size-1]:
                        if a.url is not None:
                            em.add_field(name=a.display_name, value=f'[{a.activity.name}]({a.activity.url})')
                        else:
                            em.add_field(name=a.display_name, value=f'{a.activity.name}')
                    em.set_footer(text=f'Page {b+1}/{num_segments}')
                    await ctx.send(embed=em)
            else:
                await ctx.send(f'{len(streamers)} members streaming on this server.')
        else:
            await ctx.send('No members streaming on this server.')

    @command(hidden=True)
    async def commonmembers(self, ctx, server1_id: int, server2_id: int = None):
        """Display a list of users that two servers have in common."""
        if server1_id is not None:
            if server2_id is None:
                server2 = ctx.guild
            else:
                server2 = self.bot.get_guild(server2_id)

            server1 = self.bot.get_guild(server1_id)
            if server1 is None:
                await ctx.send("I'm not in that server1.")
                return
            if server2 is None:
                await ctx.send("I'm not in that server2.")
                return

            server1_members = []
            for a in server1.members:
                server1_members.append(a.id)

            both_members = []
            for a in server2.members:
                if server1_members.__contains__(a.id):
                    both_members.append(str(a))
            both_members.sort()

            em = Embed(title="Common Members", color=0xff0000)
            em.add_field(name="Server 1: \"{}\"".format(server1.name), value="{} members".format(server1.member_count))
            em.add_field(name="Server 2: \"{}\"".format(server2.name), value="{} members".format(server2.member_count))
            em.add_field(name="{} users are in both servers:".format(len(both_members)), value="\n".join(both_members), inline=False)

            await ctx.send(embed=em)
        else:
            await ctx.send("No server specified.")


def setup(bot):
    bot.add_cog(Server(bot))
