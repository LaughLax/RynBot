from discord.ext import commands


bot = commands.Bot(command_prefix="_", owner_id=185095270986547200, help_attrs={'aliases': ['halp']})


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    extensions = ['cogs.base',
                  'cogs.chart',
                  'cogs.owner',
                  'cogs.server',
                  'cogs.my_server']
    for extension in extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}.'.format(extension))
            print(e)


with open('token.txt', 'r') as token_file:
    token = token_file.readline().strip()
bot.run(token)
