from discord import Embed, Object
from discord.ext import commands

from util import config


def is_owner():
    def predicate(ctx):
        return ctx.message.author.id == config.owner_id
    return commands.check(predicate)


def get_alpha_emoji(char):
    return {
        'a': '\U0001F1E6',
        'b': '\U0001F1E7',
        'c': '\U0001F1E8',
        'd': '\U0001F1E9',
        'e': '\U0001F1EA',
        'f': '\U0001F1EB',
        'g': '\U0001F1EC',
        'h': '\U0001F1ED',
        'i': '\U0001F1EE',
        'j': '\U0001F1EF',
        'k': '\U0001F1F0',
        'l': '\U0001F1F1',
        'm': '\U0001F1F2',
        'n': '\U0001F1F3',
        'o': '\U0001F1F4',
        'p': '\U0001F1F5',
        'q': '\U0001F1F6',
        'r': '\U0001F1F7',
        's': '\U0001F1F8',
        't': '\U0001F1F9',
        'u': '\U0001F1FA',
        'v': '\U0001F1FB',
        'w': '\U0001F1FC',
        'x': '\U0001F1FD',
        'y': '\U0001F1FE',
        'z': '\U0001F1FF'
    }.get(char, '')


async def get_message(channel, message_id):
    try:
        o = Object(id=message_id + 1)
        # don't wanna use get_message due to poor rate limit (1/1s) vs (50/1s)
        msg = await channel.history(limit=1, before=o).next()

        if msg.id != message_id:
            return None

        return msg
    except Exception:
        # TODO Slim down try/catch
        return None


def embedify_message(message):
    embed = Embed(description=message.content)
    if message.embeds:
        data = message.embeds[0]
        if data.type == 'image':
            embed.set_image(url=data.url)

    if message.attachments:
        file = message.attachments[0]
        if file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
            embed.set_image(url=file.url)
        else:
            embed.add_field(name='Attachment', value='[{}]({})'.format(file.filename, file.url), inline=False)

    embed.add_field(name='Jump to post', value=message.jump_url, inline=False)
    embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url_as(format='png'))
    embed.timestamp = message.created_at
    embed.colour = 0xff0000
    return embed
