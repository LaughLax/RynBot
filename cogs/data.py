import discord
from discord.ext import commands
from util import config

from datetime import datetime
from tzlocal import get_localzone

from util.database import Population
import asyncio
from sqlalchemy.exc import IntegrityError

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
            try:
                now = datetime.now(get_localzone()).replace(minute=0, second=0, microsecond=0)
                if now.hour != last_hour:
                    try:
                        with self.bot.db.get_session() as db:
                            pops = []
                            for server in self.bot.guilds:
                                pops.append(Population(server=server.id,
                                                       datetime=now,
                                                       user_count=server.member_count))
                            db.add_all(pops)
                    except IntegrityError as e:
                        if 'Duplicate entry' not in str(e):
                            log = self.bot.get_cog('Logs')
                            if log:
                                await log.log('Integrity error: {}'.format(e))

                    last_hour = now.hour
                await asyncio.sleep(60 * 10)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(e)
                pass

    @commands.group()
    async def data(self, ctx):
        pass

    @staticmethod
    def _db_fetch_pop_history(db, server_id):
        with db.get_session() as db:
            rows = np.array(db.query(Population.datetime, Population.user_count).\
                            filter(Population.server == server_id).\
                            order_by(Population.datetime).\
                            all())
        return rows

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
    @commands.bot_has_permissions(attach_files=True)
    async def population(self, ctx, server=None):
        if not server or ctx.message.author.id != config.owner_id:
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server))
            if not server:
                await ctx.send('I\'m not in that server.')
                return

        rows = await self.bot.loop.run_in_executor(None,
                                                   self._db_fetch_pop_history,
                                                   self.bot.db, server.id)

        with io.BytesIO() as f:
            f = await self.bot.loop.run_in_executor(self.bot.process_pool,
                                                    self.make_pop_plot,
                                                    rows, server.name, f)
            await ctx.send(file=discord.File(fp=f, filename="userchart.png"))

    @data.command()
    @commands.bot_has_permissions(attach_files=True)
    async def population2(self, ctx, server=None):
        if not server or ctx.message.author.id != config.owner_id:
            server = ctx.guild
        else:
            server = self.bot.get_guild(int(server))
            if not server:
                await ctx.send('I\'m not in that server.')
                return

        rows = await self.bot.loop.run_in_executor(None,
                                                   self._db_fetch_pop_history,
                                                   self.bot.db, server.id)

        rows[:, 0] = [x.replace(tzinfo=get_localzone()) for x in rows[:, 0]]

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

        with io.BytesIO() as f:
            plt.savefig(f, format='png')
            f.seek(0)
            await ctx.send(file=discord.File(fp=f, filename="userchart.png"))
        plt.close()


def setup(bot):
    bot.add_cog(Data(bot))
