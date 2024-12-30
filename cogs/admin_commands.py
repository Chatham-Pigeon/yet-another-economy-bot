import datetime

import discord
from discord.ext import commands
import config
from helperfunctions import isadmin, SQL_EXECUTE, dointerest, get_db_connection, get_user_data

db, cursor = get_db_connection('admin_commands')

class admincommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.check(isadmin)
    async def execute(self, ctx, execute,):
        if execute:
            try:
                cursor.execute(f"{execute}")
                data = cursor.fetchall()
                db.commit()
                await ctx.reply(f"`{execute}` \n {data}")
            except Exception as e:
                await ctx.reply(f"An error occurred: {e}")
        else:
            await ctx.reply("You need to specify a command!")
    @commands.command(hidden=True)
    @commands.check(isadmin)
    async def additem(self, ctx, displayname, itemid, cost, description, emoji):

        if displayname and itemid and cost and description and emoji:
            cursor.execute("SELECT * FROM SHOPITEMS WHERE itemid = %s", (itemid,))
            if cursor.fetchone():
                await ctx.reply("Item with that ID already exists.")
                return
            cursor.execute("INSERT INTO SHOPITEMS(displayname, itemid, cost, description, emoji) VALUES (%s, %s, %s, %s, %s)", (displayname, itemid, int(cost), description, emoji))
            db.commit()
            embed = discord.Embed(title="Item Added!",
                              colour=0x00b0f4,
                              timestamp=datetime.datetime.now())

            embed.add_field(name=f"{emoji} {displayname}",
                        value=f"**{description}**\nCost: {cost}\n-# Purchase ID: {itemid}\n",
                        inline=False)
            embed.set_footer(text=f"{config.STATIC_CREDITS}")
            await ctx.send(embed=embed)
        else:
            await ctx.reply("you are missing a value, you NEED, displayname, itemid, cost, description, emoji")
    @additem.error
    async def additem_error(self, ctx, error):
        await ctx.reply(str(error))

    @commands.command(hidden=True)
    @commands.check(isadmin)
    async def setitemcost(self, ctx, itemid, cost):
        if itemid and cost:
            cursor.execute("UPDATE SHOPITEMS SET cost = %s WHERE itemid = %s", (cost, itemid))
            db.commit()
            await ctx.reply(f"Successfully set cost of item with ID `{itemid}` to `{cost}`!")

    @commands.command(hidden=True)
    @commands.check(isadmin)
    async def givecoins(self, ctx, user, amt):

        if not user or not amt:
           await ctx.reply("You need to specify a user and an amount!")
           return

        try:
            user = await commands.UserConverter().convert(ctx, user)
        except commands.CommandError:
            await ctx.reply("Could not find the specified user.")
            return

        try:
            amt = int(amt)
        except ValueError:
            await ctx.reply("Please provide a valid amount.")
            return

        try:
            user_data = await get_user_data(ctx, ['walletAmt'])
            if not user_data:
                await ctx.reply(f"User data not found for {user.display_name}.")
                return

            cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt + %s WHERE userID = %s", (amt, user.id))
            db.commit()
            await ctx.reply(f"Successfully given {amt} coins to {user.display_name}!")

        except Exception as e:
            await ctx.reply(f"An error occurred: {e}")

    @commands.command(hidden=True)
    @commands.check(isadmin)
    async def test(self, ctx):
        await SQL_EXECUTE('UPDATE', 'USERDATA', {'walletAmt': f'walletAmt = walletAmt + {10}'},
                          {'userID': f'{ctx.author.id}'})

    @commands.command(hidden=True)
    @commands.check(isadmin)
    async def fixbank(self, ctx):
        cursor.execute("SELECT bankAmt, userID FROM USERDATA")
        bankdata = cursor.fetchall()
        for amt in bankdata:
            newamt = round(amt[0], 0)
            ctx.reply(f'newamt + bankdata[1]')
            cursor.execute("UPDATE USERDATA SET bankAmt = %s WHERE userID = %s", (newamt, amt[1]))
            db.commit()
        cursor.execute("SELECT walletAmt, userID FROM USERDATA")
        bankdata = cursor.fetchall()
        for amt in bankdata:
            newamt = round(amt[0], 0)
            ctx.reply(f'newamt + bankdata[1]')
            cursor.execute("UPDATE USERDATA SET walletAmt = %s WHERE userID = %s", (newamt, amt[1]))
            db.commit()

    @commands.command(hidden=True)
    @commands.check(isadmin)
    async def temp(self, ctx):
        await dointerest(ctx)

    @commands.command(aliases=['casino'], hidden=True)
    @commands.check(isadmin)
    async def set_casino_money(self, ctx, amt):
        cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = %s", (int(amt),))
        db.commit()
        await ctx.reply("okay")

    @commands.command(hidden=True)
    @commands.check(isadmin)
    async def givebotrights(self, ctx):
        cursor.execute("INSERT INTO USERDATA(userID, walletAmt, bankAmt, bankMax, boughtItems, currentXP, userLevel) VALUES (%s, %s, %s, %s, %s, %s, %s)",(self.bot.user.id, 0, 0, 1000, "", 0, 1))
        db.commit()


async def setup(bot):
    await bot.add_cog(admincommands(bot))
    pass
