from discord import Embed
from discord.errors import HTTPException
from discord.ext.commands import Bot

from util import misc

bot = Bot(command_prefix="self_", self_bot=True)


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
                  'cogs.stars']
    for extension in extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}.'.format(extension))
            print(e)


@bot.event
async def on_message(message):
    try:
        await bot.process_commands(message)
    except HTTPException as err:
        await message.channel.send(err)
        raise


@bot.event
async def on_reaction_add(reaction, user):
    if user.id == bot.user.id:
        # print("Reaction at " + datetime.now().strftime("%H:%M:%S"))
        global reaction_text
        if reaction.emoji == '\U0001F643' and reaction_text != '':
            await reaction.message.remove_reaction(reaction.emoji, user)
            for a in reaction_text.lower():
                if a.isalpha():
                    emoji = misc.get_alpha_emoji(a)
                    await reaction.message.add_reaction(emoji)
            reaction_text = ''


@bot.command()
async def prime(ctx, *, react: str = None):
    if react is not None:
        global reaction_text
        reaction_text = react
        # await bot.edit_message(ctx.message, 'Reaction primed. Trigger with \U0001F643')
        # await asyncio.sleep(1)
        await ctx.message.delete()


@bot.command()
async def unprime(ctx):
    global reaction_text
    reaction_text = ""
    await ctx.message.delete()


@bot.command()
async def embed(ctx):
    split = ctx.message.content.split(" ", 1)
    if len(split) > 1:
        parts = split[1].split(" | ")
        if len(parts) == 3:
            em = Embed(title=parts[0], color=0xff0000)
            em.add_field(name=parts[1], value=parts[2])
            await ctx.send(embed=em)
        if len(parts) == 4:
            em = Embed(title=parts[0], color=int(parts[3]))
            em.add_field(name=parts[1], value=parts[2])
            await ctx.send(embed=em)
    await ctx.message.delete()


with open('selftoken.txt', 'r') as token_file:
    token = token_file.readline().strip()
bot.run(token, bot=False)
