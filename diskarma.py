import discord
import os
from discord.ext import commands

# TODO Multi + and Multi -
# TODO Make sure to clear spaces out of the hash ids 'bob ++' should be 'bob' not 'bob ' 
# TODO Handle just '++' and just '--' (add karma to the bot?) (Or get the last message in the channel and add karma to the author?)
# TODO '+?' '-?' for a random amount of karma?
# TODO Can I check edited messages
# TODO Need storage
# TODO Karma user blacklist ?
# TODO Store message id?
#   When bot comes online scan history for hits until we find matching id?

bot = commands.Bot(command_prefix='>')

data = dict()

def __self_karma_check(message):
    if message.content.endswith('++') or message.content.endswith('--'):
           if message.author in message.mentions:
               return True
           return False

def __is_karma_message(message):
    id = None
    action = None
    if message.content.endswith('++'):
        id = message.content[0:-2].strip()
        action = 'add'
    elif message.content.endswith('--'):
        id = message.content[0:-2].strip()
        action = 'subtract'
    elif message.content.endswith('=='):
        id = message.content[0:-2].strip()
        action = 'show'
    return (id, action)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    id, action = __is_karma_message(message)
    if action is None:
        return

    if __self_karma_check(message):
        await message.channel.send('You can\'t karma yourself bro... Uncool')
        return

    if action == 'add':
        if id in data:
            data[id] += 1
        else:
            data[id] = 1
    elif action == 'subtract':
        if id in data:
            data[id] -= 1
        else:
            data[id] = -1
    elif action == 'show':
        if id not in data:
            data[id] = 0
    await message.channel.send('{0} has {1} karma!'.format(id, data[id]))

@bot.event
async def on_message_delete(message):
    if message.author == bot.user:
        return

    id, action = __is_karma_message(message)

    if action == None:
        return

    if __self_karma_check(message):
        await message.channel.send('You can\'t karma yourself bro... Uncool')
        return

    if action == 'add':
        if id in data:
            data[id] -= 1
        else:
            data[id] = 0
    elif action == 'subtract':
        if id in data:
            data[id] += 1
        else:
            data[id] = 0
    await message.channel.send('Karma message deleted {0} has {1} karma!'.format(id, data[id]))

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

bot.run(os.environ['BOT_KEY'])
