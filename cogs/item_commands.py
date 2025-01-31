import datetime
import discord
from discord.ext import commands
from discord.ext.commands import BucketType

import config
from helperfunctions import get_db_connection, user_items, user_data, update_user_data, update_user_items


async def djpass(ctx):
    await ctx.reply("You have the DJ role now!")
    guild = ctx.guild
    djrole = guild.get_role(config.ROLE_DJ)
    await ctx.author.add_roles(djrole)


async def serverunmute(ctx):
    await ctx.reply("You've been un server muted")
    await ctx.author.edit(mute=False)



class itemcommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Lists shop items avaliable for purchase.")
    async def shop(self,ctx, shop_page: int = 1):
        db, cursor = await get_db_connection('shop') # EXCLUSIVE USE OF SHOPITEMS
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
        useritems = await user_items(ctx.author.id, 'inventory')
        useritems.pop(0)
        db, cursor = await get_db_connection('inventory') # USE FOR EXCLUSIVELY GETTING SHOPITEMS
        if not useritems:
            await ctx.reply("User Items not found or you have none.")
            return
        if user:
            try:
                user = await commands.UserConverter().convert(ctx, user)
            except commands.CommandError:
                await ctx.reply("No user found, try @mention them.")
                return
        else:
            user = ctx.author

        embed = discord.Embed(title=f"{user.name}'s Inventory",
                              colour=0x00b0f4,
                              timestamp=datetime.datetime.now())
        for eachitem in useritems:
            cursor.execute("SELECT * FROM SHOPITEMS WHERE itemid = %s", (eachitem,))
            item = cursor.fetchone()
            print(item)
            displayname, itemid, cost, description, emoji = item
            embed.add_field(name=f"{emoji} {displayname} \n", value=f"**{description}**", inline=False)
            embed.set_footer(text=f"{config.STATIC_CREDITS}")
        await ctx.reply(embed=embed)

    @commands.command(aliasas=['purchase', ], help="Buys an item from the shop \n Ensure you use the ""PurchaseID""")
    @commands.cooldown(1, 5, BucketType.user)
    async def buy(self, ctx, itemtobuy):
        userdata = await user_data(ctx.author.id, 'buy')
        useritems = await user_items(ctx.author.id, 'buy')
        if not userdata:
            await ctx.reply("Failed to grab user data.")
        db, cursor = await get_db_connection('buy') # USE FOR EXCLUSIVELY GETTING SHOPITEMS
        cursor.execute("SELECT * FROM SHOPITEMS WHERE itemid = %s", (itemtobuy,))
        item = cursor.fetchone()
        if not item:
            await ctx.reply("Item not found.")
            return
        displayname, itemid, cost, description, emoji = item

        if not userdata['walletAmt'] >= cost:
            await ctx.reply("You don't have enough coins in your wallet for this item.")
            return
        userdata['walletAmt'] = userdata['walletAmt'] - cost
        useritems.append(itemid)
        await update_user_data(userdata)
        await update_user_items(useritems)
        await ctx.reply(f"You bought {displayname} for {cost} coins!")

    @commands.command(help="Use an item you've bought.")
    async def use(self, ctx, itemToUse):
        useritems = await user_items(ctx.author.id, 'use')

        db, cursor = await get_db_connection('use') # USE FOR EXCLUSIVELY GETTING SHOPITEMS
        cursor.execute("SELECT * FROM SHOPITEMS WHERE itemid = %s", (itemToUse,))
        item = cursor.fetchone()
        if not item:
            await ctx.reply("That item doesn't exist.")
            return
        displayname, itemid, cost, description, emoji = item

        if not useritems.__contains__(itemid):
            await ctx.reply("You don't own that item silly!")
            return
        useritems.remove(itemid)
        await update_user_items(useritems)
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

        useritems = await user_items(ctx.author.id, 'vcmute')
        if not useritems:
            ctx.reply("User data not found (Or you have no items, in which case why are you trying to use vcmute..?")
            return
        if not useritems.__contains__("servermuter"):
            await ctx.reply("You don't have a vc muter.")
            return
        useritems.remove('servermuter')
        await update_user_items(useritems, 'vcmute')
        await victim.edit(mute=True)
        await ctx.reply(f"Muted {victim.display_name}!")

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

        useritems = await user_items(ctx.author.id, 'rename')
        if not useritems:
            ctx.reply("User items not found (Or you have no items, in which case why are you trying to rename..?")
        if useritems.__contains__('renamer'):
            try:
                guild = ctx.guild
                member = guild.get_member(victim.id)
                await member.edit(nick=f"{newname}")
                await ctx.reply(f"Updated {member.display_name}")
                useritems.remove('renamer')
                await update_user_items(useritems)
            except Exception as e:
                await ctx.reply(f"An error has occured: {e}")

async def setup(bot):
    await bot.add_cog(itemcommands(bot))
