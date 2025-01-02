import discord
import mysql
from mysql.connector import Error
import config
from DISCORD_TOKEN import dbinfo

async def isadmin(ctx):
    """
    use message ctx ;3
    """
    if ctx.author.get_role(config.ROLE_ADMIN):
        return True
    else:
        return False


#  cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt + %s WHERE userID = %s", (betamt, ctx.author.id))
async def SQL_EXECUTE(action, table, values=None, conditions=None):
    """
    action = UPDATE, INSERT, DELETE, SELECT
    table = table u want to update
    values = if SELECT: LIST if update: DICTIONARY
    conditions = for things like WHERE

    returns:
    cursor.fetchone() if SELECT
    """
    if action == 'UPDATE':
        query = f'UPDATE {table} SET '
        valueslen = len(values)
        i = 0
        for key, value in values.items():
            i = i + 1
            query = query + f"{key} = '{value}'"
            if i < valueslen:
                query = query + ', '
        conlen = len(conditions)
        i = 0
        query = query + ' WHERE '
        for key, value in conditions.items():
            i = i + 1
            if type(value) == str:
                query = query + f"{key} = '{value}'"
            else:
                query = query + f"{key} = {value}"
            if i < conlen:
                query = query + ' AND '

    elif action == "INSERT":
        query = f"INSERT INTO {table} ("
        i = 0
        valueslen = len(values)
        print(query)
        if values:
            for key, value in values.items():
                i = i + 1
                query = query + key
                print(query)
                if i < valueslen:
                    print('bruh')
                    query = query + ", "
                print(query)
            query = query + ") VALUES ("
            i = 0
            for key, value in values.items():
                i += 1
                query = query + f"'{value}'"
                if i < valueslen:
                    query = query + ", "
                else:
                    query = query + ")"

    elif action == "SELECT":
        # adding the things u want to select to the query
        queries = ""
        querieslen = len(values)
        i = 0
        # values here should be a LIST, so were turning the list values into a string with ", " in the middle
        for value in values:
            i = i + 1
            queries = queries + value
            # if it ISN'T the last value, add ", " (sql will yell at you if the values end with, so it needs to be avoided
            if i < querieslen:
                queries = queries + ", "
                #add the stringified values & table to query
        query = f"SELECT {queries} FROM {table} "
        if conditions:
            condition = ""
            increm = 0
            for key, value in conditions.items():
                increm = increm + 1
                condition = condition + f"{key} = '{value}'"
                length = len(conditions)
                # avoid adding AND at the end of the conditions, otherwise SQL complains
                if increm < length:
                    condition = condition + " AND "
            #add the actual where + stringified conditions to the entire query
            query = query + f"WHERE {condition}"
    print(query)

async def dointerest(ctx):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT userID, bankAmt FROM USERDATA")
    user_data = cursor.fetchall()
    for user in user_data:
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




def get_db_connection(wherestarted=None):
    if wherestarted is None:
        wherestarted = "Undefined"
    try:
        # MySQL Connection
        db_connection = mysql.connector.pooling.connect(**dbinfo)

        if db_connection.is_connected():
            print(f"Connection at {wherestarted} to MySQL database was successful!")
            cursor = db_connection.cursor(buffered=True)
            return [db_connection, cursor]
        else:
            print(f"Failed to establish a connection to the database at {wherestarted}.")
            return None
    except Error as e:
        print(f"Error at {wherestarted} while connecting to MySQL: {e}")
        return None

db, cursor = get_db_connection('helperfunctions')


async def get_user_data(ctx, values=None, userId=None):
    """
    param 1: msg ctx/int
    param 2: LIST of values to get (empty = ALL)
    param3: if you're trying to get id of someone not author use this (user id)
    """
    if userId is None:
        user = ctx.author.id
    else:
        user = userId
    try:
        if values is None or values == "":
            query = f"SELECT * FROM USERDATA WHERE userID = {user}"
        else:
            formatted_values = ", ".join(str(item) for item in values)
            query = f"SELECT {formatted_values} FROM USERDATA WHERE userID = {user}"
        cursor.execute(query)
        data = cursor.fetchone()
        return data
    except Exception as e:
        await ctx.bot.get_channel(config.CHANNEL_LOG).send(f"<@{config.USER_CHATHAM}> :fire: :fire: :fire: FAILED TO GRAB USER DATA FOR REASON: {e} <#{ctx.channel.id}> \n")