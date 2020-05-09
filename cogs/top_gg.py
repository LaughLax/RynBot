from dbl import DBLClient
from discord.ext.commands import Cog

from util import config


class TopGG(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.token = config.top_gg_token
        self.dblpy = DBLClient(self.bot, self.token, autopost=True)


def setup(bot):
    bot.add_cog(TopGG(bot))
