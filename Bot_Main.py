from discord.ext import commands
from util import config

bot = commands.Bot(command_prefix=config.prefix,
                   owner_id=config.owner_id,
                   help_command=commands.HelpCommand(command_attrs={'aliases': ['halp']}))

if __name__ == '__main__':
    for extension in config.cogs_core:
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
        chan = bot.get_channel(config.bot_log_id)
        await chan.send("Help me <@​​​{}>! I failed to load my logging cog!".format(config.owner_id))


bot.run(config.token)
