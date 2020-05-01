from discord import ActivityType, Embed, TextChannel
from discord.ext.commands import Cog, command, has_permissions


class Server(Cog):
    def __init__(self, bot):
        self.bot = bot

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
