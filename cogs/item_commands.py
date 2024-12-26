import asyncio
import datetime
import random
import discord
from discord.ext import commands
from discord.ext.commands import BucketType, CommandOnCooldown

import config
from helperfunctions import get_db_connection

db= get_db_connection()
cursor = db.cursor()


async def djpass(ctx):
    await ctx.reply("You have the DJ role now!")
    guild = ctx.guild
    djrole = guild.get_role(config.ROLE_DJ)
    await ctx.author.add_roles(djrole)


async def serverunmute(ctx):
    await ctx.reply("You've been un server muted")
    await ctx.author.edit(mute=False)

async def addtyrobot(ctx):
    await ctx.reply("Yay! TyroBot has started working for you. Expect around 15 coins an hour.")
    cursor.execute("UPDATE USERDATA set tyrobotCount = tyrobotCount + 1 WHERE userID = %s", (ctx.author.id,))

class itemcommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Lists shop items avaliable for purchase.")
    async def shop(self,ctx, shop_page: int = 1):
        cursor.execute("SELECT * FROM SHOPITEMS")
        items = cursor.fetchall()
        items_per_page = 5
        pages = [items[i:i + items_per_page] for i in range(0, len(items), items_per_page)]

        if shop_page < 1 or shop_page > len(pages):
            await ctx.reply(f"Invalid page number. Please select a page between 1 and {len(pages)}.")
            return

        embed = discord.Embed(title="Shop")
        for item in pages[shop_page - 1]:
            displayname, itemid, cost, description, emoji = item
            embed.add_field(name=f"{emoji} {displayname}",
                            value=f"**{description}**\nCost: {cost}\n-# Purchase ID: {itemid}\n",
                            inline=False)
        embed.set_footer(text=f"Page {shop_page} of {len(pages)} | {config.STATIC_CREDITS}")
        await ctx.reply(embed=embed)

    @commands.command(aliases=['inv'], help="Shows the inventory of the specified user.")
    async def inventory(self, ctx, user=None):
        if user:
            try:
                user = await commands.UserConverter().convert(ctx, user)
                user_id = user.id
            except commands.CommandError:
                await ctx.reply("No user found, try @mention them.")
                return
        else:
            user_id = ctx.author.id
            user = ctx.author
        cursor.execute("SELECT boughtItems FROM USERDATA WHERE userID = %s", (user_id,))
        boughtItems = cursor.fetchone()
        if not boughtItems:
            await ctx.reply("User has no items.")
            return
        boughtItems = boughtItems[0]
        embed = discord.Embed(title=f"{user.name}'s Inventory",
                              colour=0x00b0f4,
                              timestamp=datetime.datetime.now())
        for eachitem in boughtItems.split():
            cursor.execute("SELECT * FROM SHOPITEMS WHERE itemid = %s", (eachitem,))
            item = cursor.fetchone()
            displayname, itemid, cost, description, emoji = item
            embed.add_field(name=f"{emoji} {displayname} \n", value=f"**{description}**", inline=False)
            embed.set_footer(text=f"{config.STATIC_CREDITS}")
        await ctx.reply(embed=embed)

    @commands.command(aliasas=['purchase', ], help="Buys an item from the shop \n Ensure you use the ""PurchaseID""")
    @commands.cooldown(1, 5, BucketType.user)
    async def buy(self, ctx, itemtobuy):
        cursor.execute("SELECT * FROM SHOPITEMS WHERE itemid = %s", (itemtobuy,))
        item = cursor.fetchone()
        if not item:
            await ctx.reply("Item not found.")
            return
        displayname, itemid, cost, description, emoji = item
        cursor.execute("SELECT walletAmt FROM USERDATA WHERE userID = %s", (ctx.author.id,))
        user_data = cursor.fetchone()
        cursor.execute("SELECT boughtItems FROM USERDATA WHERE userID = %s", (ctx.author.id,))
        boughtitems = cursor.fetchone()
        if user_data[0] >= cost:
            cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt - %s WHERE userID = %s", (cost, ctx.author.id))
            db.commit()
            updatedboughtitems = itemid + " " + boughtitems[0]
            cursor.execute("UPDATE USERDATA SET boughtItems = %s WHERE userID = %s", (updatedboughtitems, ctx.author.id))
            db.commit()
            await ctx.reply(f"You bought {displayname} for {cost} coins!")
        else:
            await ctx.reply("You don't have enough coins in your wallet for this item.")

    @commands.command(help="Use an item you've bought.")
    async def use(self, ctx, itemToUse):
        cursor.execute("SELECT * FROM SHOPITEMS WHERE itemid = %s", (itemToUse,))
        item = cursor.fetchone()
        if not item:
            await ctx.reply("That item doesn't exist.")
            return
        displayname, itemid, cost, description, emoji = item
        cursor.execute("SELECT boughtItems FROM USERDATA WHERE userID = %s", (ctx.author.id,))
        user_data = cursor.fetchone()
        if not user_data[0].__contains__(itemid):
            await ctx.reply("You don't own that item silly!")
            return
        updatedBoughItems = user_data[0].replace(itemid, "")
        cursor.execute("UPDATE USERDATA SET boughtItems = %s WHERE userID = %s", (updatedBoughItems, ctx.author.id))
        db.commit()
        # item uses (just check what item it is and call the function in item_commands.py
        if itemid == 'djpass':
            await djpass(ctx)
        if itemid == 'serverunmute':
            await serverunmute(ctx)

    @commands.command(help="Mute a server of your choice.")
    async def vcmute(self, ctx, victim):
        user = await commands.UserConverter().convert(ctx, victim)
        victim = ctx.guild.get_member(user.id)
        if not user:
            ctx.reply("User not found")
        cursor.execute("SELECT boughtItems FROM USERDATA WHERE userID = %s", (ctx.author.id,))
        user_data = cursor.fetchone()
        if not user_data:
            ctx.reply("Erm? what are u doing buddy, nono")
            return
        if user_data[0].__contains__("servermuter"):
            updatedData = user_data[0].replace("servermuter", "")
            cursor.execute("UPDATE USERDATA SET boughtItems = %s WHERE userID = %s", (updatedData, ctx.author.id))
            db.commit()
            await victim.edit(mute=True)
            await ctx.reply(f"Muted {victim.display_name}!")
        else:
            await ctx.reply("You don't have that item...")

    @commands.command(help="Rename any user.")
    async def rename(self, ctx, user, newname):
        if user:
            try:
                victim = await commands.UserConverter().convert(ctx, user)
            except commands.CommandError:
                await ctx.reply("No user found, try @mention them.")
                return
        else:
            await ctx.reply("You need to enter a user to rename.")
            return
        cursor.execute("SELECT boughtItems FROM USERDATA WHERE userID = %s", (ctx.author.id,))
        data = cursor.fetchone()
        if not data:
            await ctx.reply("User data not found.")
        if data[0].__contains__('renamer'):

            try:
                guild = ctx.guild
                member = guild.get_member(victim.id)
                await member.edit(nick=f"{newname}")
                await ctx.reply(f"Updated {member.display_name}")
                cursor.execute("UPDATE USERDATA SET boughtItems = %s WHERE userID = %s",
                               (data[0].replace('renamer', ''), ctx.author.id))
                db.commit()
            except Exception as e:
                await ctx.reply(f"An error has occured: {e}")

async def setup(bot):
    await bot.add_cog(itemcommands(bot))
