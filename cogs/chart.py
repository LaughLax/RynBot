from io import BytesIO

import matplotlib
import numpy as np
from discord import ActivityType, File
from discord.ext.commands import bot_has_permissions, BotMissingPermissions, Cog, group

matplotlib.use('Agg')
import matplotlib.pyplot as plt


class Chart(Cog):
    """Commands to make charts"""

    def __init__(self, bot):
        self.bot = bot

    @group()
    @bot_has_permissions(attach_files=True)
    async def chart(self, ctx):
        """Commands to generate charts."""

        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)    # New version
            # await ctx.invoke(self.bot.get_command('help'), 'chart')   # Old version

    @chart.error
    async def chart_error(self, ctx, error):
        if isinstance(error, BotMissingPermissions):
            await ctx.send('I don\'t have permissions to post files here. I need "Attach Files" permission to post charts.')
        else:
            await ctx.send('Error: {}'.format(error))

    @chart.command()
    async def games(self, ctx, server_id: str = None):
        """Display a bar chart of games being played on a server.

        The chart will display up to 50 games, excluding streamers and bot accounts.
        If there are more than 50 unique games being played, then a minimum number of players per game is set so that 50 or fewer games will be included on the chart."""

        # TODO Create wrapper function for games chart

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
            if not a.bot and a.activity is not None and a.activity.type == ActivityType.playing:
                if a.activity.name not in game_names:
                    game_names.append(a.activity.name)
                    game_count.append(1)
                else:
                    game_count[game_names.index(a.activity.name)] += 1

        if not game_names:
            await ctx.send("No games being played.")
            return

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

            with BytesIO() as f:
                plt.savefig(f, format='png')
                f.seek(0)
                await ctx.send(file=File(fp=f, filename="gameschart.png"))
            plt.close()
        except ValueError:
            await ctx.send("Something went wrong with fitting the graph to scale.")

    async def role_chart_wrapper(self, server_id, file_obj):
        server = self.bot.get_guild(int(server_id))
        if server is None:
            # self.bot.get_cog('Logs').log('Could not get guild with ID {}.'.format(server_id))
            raise Exception('Could not get guild with ID {}.'.format(server_id))

        role_list_db = await self.bot.db.get_custom_role_list(server_id)

        if role_list_db:
            role_list = [a for a in server.roles if not a.is_default() and a.id in role_list_db]
        else:
            role_list = [a for a in server.roles if not a.is_default()]

        role_list.reverse()
        role_names = [a.name for a in role_list]
        role_size = [len(a.members) for a in role_list]
        role_colors = [[b / 256. for b in a.color.to_rgb()] + [1.] for a in role_list]

        file_obj = await self.bot.loop.run_in_executor(self.bot.process_pool,
                                                       self.make_role_chart,
                                                       role_names, role_size, role_colors, server.name, file_obj)

        return file_obj

    @staticmethod
    def make_role_chart(role_names, role_size, role_colors, server_name, file_obj):
        top_margin = max(role_size) * 0.1

        plt.clf()
        plt.bar(range(len(role_names)), role_size, tick_label=role_names, color=role_colors, width=1., edgecolor='k')
        for i, v in enumerate(role_size):
            plt.gcf().gca().text(i, v + top_margin/2., str(v), fontsize='small', horizontalalignment='center', verticalalignment='center')
        plt.ylim(0, max(role_size) + top_margin)
        plt.xticks(rotation=90, size='xx-small')
        plt.xlabel("Role")
        plt.ylabel("Member count")
        plt.title("Role distribution for server:\n{}".format(server_name))
        plt.tight_layout()

        plt.savefig(file_obj, format='png')
        file_obj.seek(0)
        # await ctx.send(file=discord.File(fp=f, filename="rolechart.png"))
        plt.close()
        return file_obj

    @staticmethod
    def make_user_chart(join_dates, now, server_name, file_obj):
        n = len(join_dates)
        xy = np.empty((n*2), dtype=[('join', 'datetime64[us]'), ('count', 'int64')])

        xy['join'][::2] = join_dates
        xy['count'][::2] = np.ones(n)
        xy[::2].sort(order='join')
        xy['count'][::2] = np.cumsum(xy['count'][::2])

        xy[1:-1:2] = xy[2::2]
        xy['count'][1:-1:2] -= 1
        xy[-1] = (now, n)

        plt.clf()
        plt.plot(xy['join'], xy['count'])
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Member count")
        plt.title("Membership growth for server: {}\nNote: This data includes only current members.".format(server_name))
        plt.tight_layout()

        plt.savefig(file_obj, format='png')
        file_obj.seek(0)
        plt.close()
        return file_obj

    @chart.command()
    async def roles(self, ctx, server_id: str = None):
        """Display bar chart of roles on a server.

        Colors on the chart reflect the color assigned to each role.
        No attempt is made to scale the chart well.
        If the server has many roles, it may be illegible.
        If a role's name is too long, the image may fail to generate."""

        if server_id is None or server_id.lower() == "here":
            server_id = ctx.guild.id

        with BytesIO() as f:
            f = await self.role_chart_wrapper(server_id, f)
            await ctx.send(file=File(fp=f, filename="rolechart.png"))

    @chart.command()
    async def users(self, ctx, server_id: str = None):
        """Display a chart of user growth history on a server.

        This chart does not use any historical data.
        All data is obtained via the 'join date' of each member,
        meaning this chart will not reflect members who have left or been kicked from the server."""

        # TODO Complete wrapper function for users chart

        if server_id is None or server_id.lower() == "here":
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server_id))
            if server is None:
                await ctx.send("I'm not in that server.")
                return

        join_dates = [mem.joined_at for mem in server.members]

        with BytesIO() as f:
            f = await self.bot.loop.run_in_executor(self.bot.process_pool,
                                                    self.make_user_chart,
                                                    join_dates, ctx.message.created_at, server.name, f)
            await ctx.send(file=File(fp=f, filename="userchart.png"))


def setup(bot):
    bot.add_cog(Chart(bot))
