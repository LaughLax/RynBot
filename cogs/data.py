import asyncio
from datetime import datetime
from io import BytesIO

import matplotlib
import numpy as np
from discord import File
from discord.ext.commands import Cog
from discord.ext.commands import bot_has_permissions
from discord.ext.commands import group
from tzlocal import get_localzone

from util import config

matplotlib.use('Agg')
import matplotlib.pyplot as plt


class Data(Cog):
    def __init__(self, bot):
        self.bot = bot

        self.hourly_check_task = self.bot.loop.create_task(self.hourly_pop_check())

    def cog_unload(self):
        self.hourly_check_task.cancel()

    async def hourly_pop_check(self):
        # TODO Convert population check to use discord.ext.tasks framework
        await self.bot.wait_until_ready()
        last_hour = -1
        while not self.bot.is_closed():
            try:
                now = datetime.now(get_localzone()).replace(minute=0, second=0, microsecond=0)
                if now.hour != last_hour:
                    for server in self.bot.guilds:
                        await self.bot.db.add_population_row(server.id,
                                                             now,
                                                             server.member_count)
                    last_hour = now.hour
                await asyncio.sleep(60 * 10)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(e)
                pass

    @group()
    async def data(self, ctx):
        pass

    @staticmethod
    def make_pop_plot(pop_rows, server_name, file_obj):
        plt.clf()
        plt.plot(pop_rows[:, 0], pop_rows[:, 1])
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Member count")
        plt.title("Membership growth for server: {0}".format(server_name))
        plt.tight_layout()

        plt.savefig(file_obj, format='png')
        plt.close()

        file_obj.seek(0)
        return file_obj

    @data.command()
    @bot_has_permissions(attach_files=True)
    async def population(self, ctx, server=None):
        # TODO Complete wrapper for population chart
        
        if not server or ctx.message.author.id != config.owner_id:
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server))
            if not server:
                await ctx.send('I\'m not in that server.')
                return

        rows = await self.bot.db.get_population_history(server.id)
        rows = np.array(rows)

        with BytesIO() as f:
            f = await self.bot.loop.run_in_executor(self.bot.process_pool,
                                                    self.make_pop_plot,
                                                    rows, server.name, f)
            await ctx.send(file=File(fp=f, filename="userchart.png"))

    @data.command()
    @bot_has_permissions(attach_files=True)
    async def population2(self, ctx, server=None):
        # TODO Create wrapper for population2 chart
        
        if not server or ctx.message.author.id != config.owner_id:
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server))
            if not server:
                await ctx.send('I\'m not in that server.')
                return

        rows = await self.bot.db.get_population_history(server.id)
        rows = np.array(rows)

        tz_local = get_localzone()
        rows[:, 0] = [x.replace(tzinfo=tz_local) for x in rows[:, 0]]

        members = []
        for a in server.members:
            members.append(a)
        n = len(members)

        await asyncio.sleep(0)

        xy = np.empty((n*2), dtype=[('join', 'datetime64[us]'), ('count', 'int64')])
        xy['join'][::2] = list(map(lambda mem: mem.joined_at, members))
        xy['count'][::2] = np.ones(n)
        xy[::2].sort(order='join')
        xy['count'][::2] = np.cumsum(xy['count'][::2])

        xy[1:-1:2] = xy[2::2]
        xy['count'][1:-1:2] -= 1
        xy[-1] = (ctx.message.created_at, n)

        await asyncio.sleep(0)

        plt.clf()
        plt.plot(xy['join'], xy['count'], ':k',
                 rows[:, 0], rows[:, 1], '-k')
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Member count")
        plt.title("Membership growth for server: {0.name}".format(server))
        plt.tight_layout()

        with BytesIO() as f:
            plt.savefig(f, format='png')
            f.seek(0)
            await ctx.send(file=File(fp=f, filename="userchart.png"))
        plt.close()


def setup(bot):
    bot.add_cog(Data(bot))
