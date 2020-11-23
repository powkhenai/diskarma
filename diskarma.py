"""A simple bot to manage 'karma' on a discord server"""
import os
import discord
import psycopg2
import regex
from psycopg2.sql import Identifier, SQL
from discord.ext import commands
from swdb import SummonersWarDB

# TODO Handle just '++' and just '--' (add karma to the bot?) 
#   (Or get the last message in the channel and add karma to the author?)
# TODO '+?' '-?' for a random amount of karma?
# TODO Can I check edited messages
# TODO Karma user blacklist ?
# TODO Store message id?
# TODO Karma attack?
# TODO Karma reason?
# TODO Spend karma to reduce karma? (???)
# TODO I should probably catch SIGTERM and properly close my DB connection
#   When bot comes online scan history for hits until we find matching id?

DATABASE_URL = os.environ['DATABASE_URL']

TABLE_NAME = 'test'
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()

bot = commands.Bot(command_prefix='>')

def __self_karma_check(action, message):
    """Check if a user is trying to give themselves karma so we can stop them!"""
    if action in ('add', 'subtract'):
        if message.author in message.mentions:
            return True
        return False

# We need to check if discord added an ! to our id noting we're using a nickname, and then remove it...
def __id_cleanse(user_id):
    """Helper for trying to make mention ids more consistent to keep karma scores sane"""
    if regex.match('^<@!\d\d\d+>$', user_id):
        return user_id.replace('!', '')
    return user_id

def __is_karma_message(message):
    """Helper method to determine if a message is a karma message"""
    user_id = None
    action = None
    count = 0
    # This regex is a little convoluted so it can handle "I need a +15 rune ++++"
    result = regex.match(r'^((?:[\+]*[^\+]*[\+]*[^\+]+)*+)(\+\++)$', message.content)
    if result:
        user_id = __id_cleanse(result.group(1).strip())
        action = 'add'
        count = len(result.group(2)) - 1
    result = regex.match(r'^((?:[\-]*[^\-]*[\-]*[^\-]+)*+)(\-\-+)$', message.content)
    if result:
        user_id = __id_cleanse(result.group(1).strip())
        action = 'subtract'
        count = len(result.group(2)) - 1
    if message.content.endswith('=='):
        user_id = __id_cleanse(message.content[0:-2].strip())
        action = 'show'
    return (user_id, action, count)

def __db_insert(id, score):
    """Database helper method for INSERT"""
    cur.execute(SQL("INSERT into {} (id, score) VALUES (%s, %s);").format(Identifier(TABLE_NAME)), (user_id, score))
    conn.commit()

def __db_update(user_id, score):
    """Database helper method for UPDATE"""
    cur.execute(SQL("UPDATE {} SET score = %s WHERE id = %s;").format(Identifier(TABLE_NAME)), (score, user_id))
    conn.commit()

def __db_delete(user_id):
    """Database helper method for DELETE"""
    cur.execute(SQL("DELETE FROM {} WHERE id = %s;").format(Identifier(TABLE_NAME)), (user_id,))
    conn.commit()

@bot.command(hidden=True)
async def delete(ctx):
    """Bot command to delete and entry from the karma database, this is permanent"""
    user_id = ctx.message.content[8:]
    __db_delete(user_id)
    await ctx.send('All karma data for "{}" has been deleted. ByeBye!'.format(user_id))

@bot.command(description='Get a karma report as a DM', brief='Get a karma report as a DM')
async def karma(ctx):
    """Bot command to PM the user a full digest of all current karma totals"""
    cur.execute(SQL("SELECT * FROM {};").format(Identifier(TABLE_NAME)),())
    results = cur.fetchall()
    response = 'Your requested Karma digest:\n'
    for result in results:
        response = '{}      {}:{}\n'.format(response, result[0], result[1])
    await ctx.send("Alright, sending {} a karma digest as a DM".format(ctx.author.display_name))
    await ctx.author.send(response)

@bot.command(description='Take a Summoners war awakened monster name, and tell me what monster it is', brief='What monster is this name')
async def who_is(ctx):
    """Bot command to cross reference monster names in Summoners War"""
    name = ctx.message.content[8:]
    sw = SummonersWarDB()
    mon_dict = sw.who_is(name)
    monster = discord.Embed(title=mon_dict['title'])
    monster.set_image(url=mon_dict['set_image'])
    await ctx.send(embed=monster)

@bot.event
async def on_message(message):
    """When a message is sent on the server, check to see if it's a karma message and add or remove karma"""
    if message.author == bot.user:
        return

    user_id, action, count = __is_karma_message(message)
    score = 0
    if action is None:
        await bot.process_commands(message)
        return

    if __self_karma_check(action, message):
        await message.channel.send('You can\'t karma yourself bro... Uncool')
        return

    cur.execute(SQL("SELECT * FROM {} WHERE id=%s;").format(Identifier(TABLE_NAME)), (user_id,))
    results = cur.fetchall()

    if action == 'add':
        if not results:
            score += count
            __db_insert(user_id, score)
        else:
            score = results[0][1] + count
            __db_update(user_id, score)
    elif action == 'subtract':
        if not results:
            score -= count
            __db_insert(user_id, score)
        else:
            score = results[0][1] - count
            __db_update(user_id, score)
    elif action == 'show':
        if not results:
            __db_insert(user_id, score)
        else:
            score = results[0][1]
    await message.channel.send('{0} has {1} karma!'.format(user_id, score))

@bot.event
async def on_message_delete(message):
    """When a message is deleted, check to see if it was a karma message and reverse its changes"""
    if message.author == bot.user:
        return

    user_id, action, count = __is_karma_message(message)
    score = 0
    if action == None:
        return

    if __self_karma_check(action, message):
        await message.channel.send('You can\'t karma yourself bro... Uncool')
        return

    cur.execute(SQL("SELECT * FROM {} WHERE id=%s;").format(Identifier(TABLE_NAME)), (user_id,))
    results = cur.fetchall()

    if action == 'add':
        if not results:
            __db_insert(user_id, score - count)
        else:
            score = results[0][1] - count
            __db_update(user_id, score)
    elif action == 'subtract':
        if not results:
            __db_insert(user_id, score + count)
        else:
            score = results[0][1] + count
            __db_update(user_id, score)
    elif action == 'show':
        if not results:
            __db_insert(user_id, score)
        else:
            score = results[0][1]

    await message.channel.send('A gift of Karma has been rescinded... {0} has {1} karma!'.format(user_id, score))

@bot.event
async def on_ready():
    """Make sure the database table exists, and if not create it."""
    cur.execute("select exists(select * from information_schema.tables where table_name=%s)", ('test',))
    if not cur.fetchone()[0]:
        cur.execute("CREATE TABLE test (id varchar PRIMARY KEY, score integer);")
    conn.commit()

bot.run(os.environ['BOT_KEY'])
