import discord.ui
import mysql
from discord.ui import View
from mysql.connector import Error
import config
from DISCORD_TOKEN import dbinfo


async def isadmin(ctx):
    """
    use message ctx ;3
    """
    if ctx.author.get_role(config.ROLE_ADMIN) or ctx.author.id == config.USER_CHATHAM:
        return True
    else:
        return False




async def dointerest(ctx):
    db, cursor = await get_db_connection()
    cursor.execute("SELECT userID, bankAmt FROM USERDATA")
    userdata = cursor.fetchall()
    for user in userdata:
        userID, bankAmt = user
        if bankAmt >= 0:
            interest = bankAmt * 0.02
            bankAmt += interest
            bankAmt = round(bankAmt)
            cursor.execute("UPDATE USERDATA SET bankAmt = %s WHERE userID = %s", (bankAmt, userID))
            db.commit()
    db.close()

async def send_log(ctx, info=None):
    """
    param 1: message ctx
    param 2: other info to attach to log (optional)
    """
    content = f"**{ctx.author.display_name}** used `{ctx.message.content}`."
    if info:
        content = content + f"Extra Info: {info}"
    await ctx.bot.get_channel(config.CHANNEL_LOG).send(
        content=content)

async def get_db_connection(wherestarted=None):
    """
    returns a database connection & cursor
    param 1: location of code where started (optional)
    """
    if wherestarted is None:
        wherestarted = "Undefined"
    items = []
    if config.DB_CONNECTION is None: # always true on first connection
        config.DB_CONNECTION = mysql.connector.connect(**dbinfo)
        msg = f"DB connection initial connection successful: **{wherestarted}**"
        items = [config.DB_CONNECTION, config.DB_CONNECTION.cursor(buffered=True)]
    elif config.DB_CONNECTION.is_connected(): #db is already first initalised and is connected and (hopefully) working
        msg = f"DB return successful: **{wherestarted}**"
        items = [config.DB_CONNECTION, config.DB_CONNECTION.cursor(buffered=True)]
    else:
        try:
            config.DB_CONNECTION = mysql.connector.connect(**dbinfo)
            if config.DB_CONNECTION.is_connected: # db was previously disconnected and nnow reconnected
                msg = f"DB reconnection successful: **{wherestarted}**"
                items = [config.DB_CONNECTION, config.DB_CONNECTION.cursor(buffered=True)]
            else: # db failed to reconnect
                msg = f"<@{config.USER_CHATHAM}> db failed to reconnect but didnt cause an exception: **{wherestarted}**"
        except:
            msg = f" <@{config.USER_CHATHAM}> DB CONNECTION FAILED: **{wherestarted}**"
    if config.DEBUG:
        print(msg)
        await config.CONFIG_BOT.get_channel(config.CHANNEL_LOG).send(f":water: :water: water: {msg}")
    return items


async def user_items(userId, wherefrom = 'Undefined') -> list:
    """
    param 1: userId of the users items you want
    parm 2: where the call came from (optional)
    returns a list of all the users items + their userID at the 0th index
    typically used in conjunction with update_user_items
    """
    db, cursor = await get_db_connection(f'user_items,, {wherefrom}')
    cursor.execute("SELECT boughtItems FROM USERDATA WHERE userID = %s", (userId,))
    itemstuple = cursor.fetchone()
    itemsstring = itemstuple[0]
    itemslist: list = itemsstring.split()
    itemslist.insert(0, userId)
    return itemslist

async def update_user_items(itemlist: list, wherefrom = 'Undefined'):
    """
    param 1: list of items (and userId at 0th index
    param 2: where the call came from (optional)
    update a users bought items with items inside the list,
    likely you should pass a list with ALL the list items from the user_data function call
    """
    db, cursor = await get_db_connection(f'update_user_items,, {wherefrom}')
    userId = itemlist.pop(0)
    items = ' '.join(itemlist)
    cursor.execute("UPDATE USERDATA SET boughtItems = %s WHERE userID = %s", (items, userId))
    db.commit()


async def user_data(userId, wherefrom ='Undefined'):
    """
    param 1: userid of the user's data you want, likely ctx.author.id
    param 2: where the call came from (optional)
    returns a dictionary of the users data, uses the direct names of db column names
    typically in conjunction with update_user_data to grab & update data
    """
    try:
        db, cursor = await get_db_connection(f'user_data,, {wherefrom}')
        cursor.execute("SELECT * FROM USERDATA WHERE userID = %s", (userId,))
        userdata = cursor.fetchone()
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 's10052_economy' AND TABLE_NAME = 'USERDATA'")
        table_data = [row[0] for row in cursor.fetchall()]
        userdict = {}
        for i in range(len(userdata)):
            userdict[table_data[i]] = userdata[i]
        userdict['userID'] = userId
        return userdict
    except Exception as e:
        await config.CONFIG_BOT.get_channel(config.CHANNEL_LOG).send(f"<@{config.USER_CHATHAM}> :fire: :fire: :fire: FAILED TO GRAB USER DATA FOR REASON: {e} '{wherefrom}' \n")


async def update_user_data(userdict: dict, wherefrom ='Undefined'):
    """
    param 1: dictionary of user data
    param 2: where the call came from (optional)
    update a users data with all data inside the dict,
    likely you should pass a dictionary with ALL the users data from user_data function call
    """
    try:
        db, cursor = await get_db_connection(f'update_user_data,, {wherefrom}')
        userID = userdict['userID']
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 's10052_economy' AND TABLE_NAME = 'USERDATA'")
        table_data = [row[0] for row in cursor.fetchall()]
        for key, value in userdict.items():
            if not table_data.__contains__(key):
                print("TRIED TO UPDATE NON EXISTANT USERDATA COLUMN ! ! !")
                continue
            query = f"UPDATE USERDATA SET {key} = %s WHERE userID = %s" # ddont replace {key} with %s it breaks for soemr reason
            cursor.execute(query, (value, userID))
        db.commit()
    except Exception as e:
        await config.CONFIG_BOT.get_channel(config.CHANNEL_LOG).send(f"<@{config.USER_CHATHAM}> :fire: :fire: :fire: FAILED TO GRAB USER DATA FOR REASON: {e} '{wherefrom}' \n")


async def createView(viewList: dict):
    view: discord.ui.View = View()
    for i in viewList.values():
        view.add_item(i)
    return view


