import discord
from discord.ext import commands
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class Chart:
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.bot_has_permissions(attach_files=True)
    async def chart(self, ctx):
        """Commands in this group generate charts."""

        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command('help'), 'chart')

    @chart.error
    async def chart_error(self, ctx, error):
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send('I don\'t have permissions to post files here. I need "Attach Files" permission to post charts.')
        else:
            await ctx.send('Error: {}'.format(error))

    @chart.command()
    async def games(self, ctx, server_id: str = None):
        """A bar chart of games being played on a server.

        The chart will display up to 50 games, excluding streamers and bot accounts.
        If there are more than 50 unique games being played, then a minimum number of players per game is set so that 50 or fewer games will be included on the chart."""

        if server_id is None or server_id.lower() == "here":
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server_id))
            if server is None:
                await ctx.send("I'm not in that server.")
                return

        game_names = []
        game_count = []
        for a in server.members:
            if not a.bot and a.game is not None and a.game.type == 0:
                if a.game.name not in game_names:
                    game_names.append(a.game.name)
                    game_count.append(1)
                else:
                    game_count[game_names.index(a.game.name)] += 1

        cutoff = 0
        while len(game_names) > 50:
            cutoff += 1
            copy = game_names.copy()
            for g in copy:
                ind = game_names.index(g)
                if game_count[ind] <= cutoff:
                    game_names.pop(ind)
                    game_count.pop(ind)

        game_names, game_count = zip(*sorted(zip(game_names, game_count)))

        plt.clf()
        plt.bar(range(len(game_names)), game_count, tick_label=game_names, width=1., edgecolor='k')
        plt.xticks(rotation=90, size='xx-small')
        plt.xlabel("Game (top {} shown)".format(len(game_names)))
        plt.ylabel("# of Members Playing (min. {})".format(cutoff+1))
        plt.title("Games being played on server:\n{}".format(server.name))
        try:
            plt.tight_layout()

            with io.BytesIO() as f:
                plt.savefig(f, format='png')
                await ctx.send(file=discord.File(fp=f.getbuffer(), filename="gameschart.png"))
        except ValueError:
            await ctx.send("Something went wrong with fitting the graph to scale.")

    @chart.command()
    async def games_pie(self, ctx, server_id: str = None):
        """A pie chart of games being played on a server.

        The chart will display up to 10 games, excluding streamers and bot accounts.
        If there are more than 10 unique games being played, a minimum number of players per game is set so that 10 or fewer games will be included on the chart."""

        if server_id is None or server_id.lower() == "here":
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server_id))
            if server is None:
                await ctx.send("I'm not in that server.")
                return

        game_names = []
        game_count = []
        for a in server.members:
            if not a.bot and a.game is not None and a.game.type == 0:
                if a.game.name not in game_names:
                    game_names.append(a.game.name)
                    game_count.append(1)
                else:
                    game_count[game_names.index(a.game.name)] += 1

        cutoff = 0
        other_count = 0
        while len(game_names) >= 10:
            cutoff += 1
            copy = game_names.copy()
            for g in copy:
                ind = game_names.index(g)
                if game_count[ind] == cutoff:
                    game_names.pop(ind)
                    game_count.pop(ind)
                    other_count += cutoff

        if other_count > 0:
            game_names.append("Other")
            game_count.append(other_count)
        # game_names, game_count = zip(*sorted(zip(game_names, game_count)))

        plt.clf()
        patches, texts = plt.pie(game_count, labels=game_names, shadow=True)
        # for t in texts:
        # t.set_size('x-small')
        plt.title("Games being played on server:\n{}".format(server.name))
        plt.axis('scaled')

        with io.BytesIO() as f:
            plt.savefig(f, format='png')
            await ctx.send(file=discord.File(fp=f.getbuffer(), filename="gameschart.png"))

    @chart.command()
    async def roles(self, ctx, server_id: str = None):
        """A bar chart of roles on a server.

        Colors on the chart reflect the color assigned to each role.
        No attempt is made to scale the chart well.
        If the server has many roles, it may be illegible.
        If a role's name is too long, the image may fail to generate."""

        if server_id is None or server_id.lower() == "here":
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server_id))
            if server is None:
                await ctx.send("I'm not in that server.")
                return

        role_list = [a for a in server.role_hierarchy if not a.is_default()]
        role_size = [len(a.members) for a in role_list]
        role_colors = [[b / 256. for b in a.color.to_rgb()] + [1.] for a in role_list]

        plt.clf()
        plt.bar(range(len(role_list)), role_size, tick_label=role_list, color=role_colors, width=1., edgecolor='k')
        plt.xticks(rotation=90, size='xx-small')
        plt.xlabel("Role")
        plt.ylabel("Member count")
        plt.title("Role distribution for server:\n{}".format(server.name))
        plt.tight_layout()

        with io.BytesIO() as f:
            plt.savefig(f, format='png')
            await ctx.send(file=discord.File(fp=f.getbuffer(), filename="rolechart.png"))

    @chart.command()
    async def users(self, ctx, server_id: str = None):
        """A chart of user growth history on a server.

        This chart does not use any historical data.
        All data is obtained via the 'join date' of each member,
        meaning this chart will not reflect members who have left or been kicked from the server."""

        if server_id is None or server_id.lower() == "here":
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server_id))
            if server is None:
                await ctx.send("I'm not in that server.")
                return

        members = []
        for a in server.members:
            members.append(a)

        members.sort(key=lambda mem: mem.joined_at)
        (x, y) = ([], [])
        for m in range(members.__len__()):
            if m > 0:
                x.append(members[m].joined_at)
                y.append(m)
            x.append(members[m].joined_at)
            y.append(m+1)
        x.append(ctx.message.created_at)
        y.append(len(members))

        plt.clf()
        plt.plot(x, y)
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Member count")
        plt.title("Membership growth for server: {0.name}\nNote: This data includes only current members.".format(server))
        plt.tight_layout()

        with io.BytesIO() as f:
            plt.savefig(f, format='png')
            await ctx.send(file=discord.File(fp=f.getbuffer(), filename="userchart.png"))

    # @chart.command()
    # async def nothing(self, ctx):
        # await ctx.send('This command actually does nothing.')


def setup(bot):
    bot.add_cog(Chart(bot))
