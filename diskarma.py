import discord
import os
import psycopg2
import regex
from psycopg2.sql import Identifier, SQL
from discord.ext import commands

# TODO Handle just '++' and just '--' (add karma to the bot?) (Or get the last message in the channel and add karma to the author?)
# TODO '+?' '-?' for a random amount of karma?
# TODO Can I check edited messages
# TODO Karma user blacklist ?
# TODO Store message id?
# TODO Karma attack?
# TODO Spend karma to reduce karma? (???)
#   When bot comes online scan history for hits until we find matching id?

DATABASE_URL = os.environ['DATABASE_URL']

TABLE_NAME = 'test'
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()

bot = commands.Bot(command_prefix='>')

def __self_karma_check(action, message):
    if action == 'add' or action == 'subtract':
           if message.author in message.mentions:
               return True
           return False

def __is_karma_message(message):
    id = None
    action = None
    count = 0
    # This regex is a little convoluted so it can handle "I need a +15 rune ++++"
    result = regex.match('^((?:[\+]*[^\+]*[\+]*[^\+]+)*+)(\+\++)$', message.content)
    if result:
        id = result.group(1).strip()
        action = 'add'
        count = len(result.group(2)) - 1
    result = regex.match('^((?:[\-]*[^\-]*[\-]*[^\-]+)*+)(\-\-+)$', message.content)
    if result:
        id = result.group(1).strip()
        action = 'subtract'
        count = len(result.group(2)) - 1
    if message.content.endswith('=='):
        id = message.content[0:-2].strip()
        action = 'show'
    return (id, action, count)

def __db_insert(id, score):
    cur.execute(SQL("INSERT into {} (id, score) VALUES (%s, %s);").format(Identifier(TABLE_NAME)), (id, score))
    conn.commit()

def __db_update(id, score):
    cur.execute(SQL("UPDATE {} SET score = %s WHERE id = %s;").format(Identifier(TABLE_NAME)), (score, id))
    conn.commit()

def __db_delete(id):
    cur.execute(SQL("DELETE FROM {} WHERE id = %s;").format(Identifier(TABLE_NAME)), (id,))
    conn.commit()

@bot.command(hidden=True)
async def delete(ctx):
    id = ctx.message.content[8:]
    __db_delete(id)
    await ctx.send('All karma data for "{}" has been deleted. ByeBye!'.format(id))

@bot.command(description='Get a karma report as a DM', brief='Get a karma report as a DM')
async def karma(ctx):
    cur.execute(SQL("SELECT * FROM {};").format(Identifier(TABLE_NAME)),())
    results = cur.fetchall()
    response = 'Your requested Karma digest:\n'
    for result in results:
        response = '{}      {}:{}\n'.format(response, result[0], result[1])
    await ctx.send("Alright, sending {} a karma digest as a DM".format(ctx.author.display_name))
    await ctx.author.send(response)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    id, action, count = __is_karma_message(message)
    score = 0
    if action is None:
        await bot.process_commands(message)
        return

    if __self_karma_check(action, message):
        await message.channel.send('You can\'t karma yourself bro... Uncool')
        return

    cur.execute(SQL("SELECT * FROM {} WHERE id=%s;").format(Identifier(TABLE_NAME)), (id,))
    results = cur.fetchall()

    if action == 'add':
        if not results:
            score += count
            __db_insert(id, score)
        else:
            score = results[0][1] + count
            __db_update(id, score)
    elif action == 'subtract':
        if not results:
            score -= count
            __db_insert(id, score)
        else:
            score = results[0][1] - count
            __db_update(id, score)
    elif action == 'show':
        if not results:
            __db_insert(id, score)
        else:
            score = results[0][1]
    await message.channel.send('{0} has {1} karma!'.format(id, score))

@bot.event
async def on_message_delete(message):
    if message.author == bot.user:
        return

    id, action, count = __is_karma_message(message)
    score = 0
    if action == None:
        return

    if __self_karma_check(action, message):
        await message.channel.send('You can\'t karma yourself bro... Uncool')
        return

    cur.execute(SQL("SELECT * FROM {} WHERE id=%s;").format(Identifier(TABLE_NAME)), (id,))
    results = cur.fetchall()

    if action == 'add':
        if not results:
            __db_insert(id, score - count)
        else:
            score = results[0][1] - count
            __db_update(id, score)
    elif action == 'subtract':
        if not results:
            __db_insert(id, score + count)
        else:
            score = results[0][1] + count
            __db_update(id, score)
    elif action == 'show':
        if not results:
            __db_insert(id, score)
        else:
            score = results[0][1]

    await message.channel.send('A gift of Karma has been rescinded... {0} has {1} karma!'.format(id, score))

@bot.event
async def on_ready():
    cur.execute("select exists(select * from information_schema.tables where table_name=%s)", ('test',))
    if not cur.fetchone()[0]:
        cur.execute("CREATE TABLE test (id varchar PRIMARY KEY, score integer);")
    conn.commit()

bot.run(os.environ['BOT_KEY'])
