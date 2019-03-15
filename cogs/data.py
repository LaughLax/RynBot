import discord
from discord.ext import commands
from util import config

from datetime import datetime
from tzlocal import get_localzone

from util.database import Population
import asyncio

import numpy as np
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class Data(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.hourly_check_task = self.bot.loop.create_task(self.hourly_pop_check())

    def cog_unload(self):
        self.hourly_check_task.cancel()

    async def hourly_pop_check(self):
        await self.bot.wait_until_ready()
        last_hour = -1
        while not self.bot.is_closed():
            now = datetime.now(get_localzone()).replace(minute=0, second=0, microsecond=0)
            if now.hour != last_hour:
                with self.bot.db.get_session() as db:
                    pops = []
                    for server in self.bot.guilds:
                        pops.append(Population(server=server.id,
                                               datetime=now,
                                               user_count=server.member_count))
                    db.add_all(pops)

                last_hour = now.hour
            await asyncio.sleep(60 * 10)

    @commands.group()
    async def data(self, ctx):
        pass

    @data.command()
    async def population(self, ctx, server=None):
        if not server or ctx.message.author.id != config.owner_id:
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server))

        with self.bot.db.get_session() as db:
            rows = np.array(db.query(Population.datetime, Population.user_count).\
                            filter(Population.server == server.id).\
                            order_by(Population.datetime).\
                            all())

        plt.clf()
        plt.plot(rows[:, 0], rows[:, 1])
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Member count")
        plt.title("Membership growth for server: {0.name}".format(server))
        plt.tight_layout()

        with io.BytesIO() as f:
            plt.savefig(f, format='png')
            await ctx.send(file=discord.File(fp=f.getbuffer(), filename="userchart.png"))
        plt.close()

    @data.command()
    async def population2(self, ctx, server=None):
        if not server or ctx.message.author.id != config.owner_id:
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server))
            if server is None:
                await ctx.send("I'm not in that server.")
                return

        with self.bot.db.get_session() as db:
            rows = np.array(db.query(Population.datetime, Population.user_count).\
                            filter(Population.server == server.id).\
                            order_by(Population.datetime).\
                            all())

        f = lambda x: x.replace(tzinfo=get_localzone())
        rows[:, 0] = np.array(list(map(f, rows[:, 0])))

        members = []
        for a in server.members:
            members.append(a)
        n = len(members)

        xy = np.empty((n*2), dtype=[('join', 'datetime64[us]'), ('count', 'int64')])
        xy['join'][::2] = list(map(lambda mem: mem.joined_at, members))
        xy['count'][::2] = np.ones(n)
        xy[::2].sort(order='join')
        xy['count'][::2] = np.cumsum(xy['count'][::2])

        xy[1:-1:2] = xy[2::2]
        xy['count'][1:-1:2] -= 1
        xy[-1] = (ctx.message.created_at, n)

        plt.clf()
        plt.plot(xy['join'], xy['count'], ':k',
                 rows[:, 0], rows[:, 1], '-k')
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Member count")
        plt.title("Membership growth for server: {0.name}".format(server))
        plt.tight_layout()

        with io.BytesIO() as f:
            plt.savefig(f, format='png')
            await ctx.send(file=discord.File(fp=f.getbuffer(), filename="userchart.png"))
        plt.close()


def setup(bot):
    bot.add_cog(Data(bot))
