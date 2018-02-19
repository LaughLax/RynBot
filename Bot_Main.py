from discord.ext import commands
from util import misc


bot = commands.Bot(command_prefix="_", owner_id=185095270986547200, help_attrs={'aliases': ['halp']})

if __name__ == '__main__':
    for extension in misc.base_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}.'.format(extension))
            print(e)


@bot.event
async def on_ready():

    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    if 'cogs.logs' not in bot.extensions:
        print('Logs cog failed to load!')
        chan = bot.get_channel(misc.bot_log_id)
        await chan.send("Help me <@​​​{}>! I failed to load my logging cog!".format(misc.ryn_id))


with open('token.txt', 'r') as token_file:
    token = token_file.readline().strip()
bot.run(token)
