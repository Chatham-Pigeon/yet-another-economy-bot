import discord
import config
import sqlite3

db = sqlite3.connect("./economy.db")
cursor = db.cursor()


async def isadmin(ctx):
    if ctx.author.get_role(config.ROLE_ADMIN):
        return True
    else:
        return False


#  cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt + ? WHERE userID = ?", (betamt, ctx.author.id))
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

async def send_log(ctx, info=None):
    content = f"**{ctx.author.display_name}** used `{ctx.command}`."
    if info:
        content = content + f"Extra Info: {info}"
    await ctx.bot.get_channel(config.CHANNEL_LOG).send(
        content=content)
