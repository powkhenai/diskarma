import discord
import os
import psycopg2
from psycopg2.sql import Identifier, SQL
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

DATABASE_URL = os.environ['DATABASE_URL']

TABLE_NAME = 'test'
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()

bot = commands.Bot(command_prefix='>')

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

def __db_insert(id, score):
    cur.execute(SQL("INSERT into {} (id, score) VALUES (%s, %s);").format(Identifier(TABLE_NAME)), (id, score))
    conn.commit()

def __db_update(id, score):
    cur.execute(SQL("UPDATE {} SET score = %s WHERE id = %s;").format(Identifier(TABLE_NAME)), (score, id))
    conn.commit()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    id, action = __is_karma_message(message)
    score = 0
    if action is None:
        return

    if __self_karma_check(message):
        await message.channel.send('You can\'t karma yourself bro... Uncool')
        return

    cur.execute(SQL("SELECT * FROM {} WHERE id=%s;").format(Identifier(TABLE_NAME)), (id,))
    results = cur.fetchall()

    if action == 'add':
        if not results:
            score += 1
            __db_insert(id, score)
        else:
            score = results[0][1] + 1
            __db_update(id, score)
    elif action == 'subtract':
        if not results:
            score -= 1
            __db_insert(id, score)
        else:
            score = results[0][1] - 1
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

    id, action = __is_karma_message(message)
    score = 0
    if action == None:
        return

    if __self_karma_check(message):
        await message.channel.send('You can\'t karma yourself bro... Uncool')
        return

    cur.execute(SQL("SELECT * FROM {} WHERE id=%s;").format(Identifier(TABLE_NAME)), (id,))
    results = cur.fetchall()

    if action == 'add':
        if not results:
            __db_insert(id, score-1)
        else:
            score = results[0][1] - 1
            __db_update(id, score)
    elif action == 'subtract':
        if not results:
            __db_insert(id, score+1)
        else:
            score = results[0][1] + 1
            __db_update(id, score)
    elif action == 'show':
        if not results:
            __db_insert(id, score)
        else:
            score = results[0][1]

    await message.channel.send('A gift of Karma has been rescinded... {0} has {1} karma!'.format(id, score))

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.event
async def on_ready():
    cur.execute("select exists(select * from information_schema.tables where table_name=%s)", ('test',))
    if not cur.fetchone()[0]:
        cur.execute("CREATE TABLE test (id varchar PRIMARY KEY, score integer);")
    conn.commit()

bot.run(os.environ['BOT_KEY'])
