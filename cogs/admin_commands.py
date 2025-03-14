import datetime

import discord
from discord.ext import commands
from discord.ui import Button, View

import config
from helperfunctions import isadmin, dointerest, get_db_connection, createView, user_data, update_user_data


class admincommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.check(isadmin)
    async def sqlexecute(self, ctx, execute):
        db, cursor = await get_db_connection('sqlexecute') #im too fucking lazy to do these
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
        db, cursor = await get_db_connection('additem') #okay sure ig
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
        db, cursor = await get_db_connection('setitemcost') #im too fucking lazy to do these
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
            userdata = await user_data(user.id, 'givecoins')
            if not userdata:
                await ctx.reply(f"User data not found for {user.display_name}.")
                return
            userdata['walletAmt'] = userdata['walletAmt'] + amt
            await ctx.reply(f"Successfully given {amt} coins to {user.display_name}!")
            await update_user_data(userdata)
        except Exception as e:
            await ctx.reply(f"An error occurred: {e}")


    @commands.command(hidden=True)
    @commands.check(isadmin)
    async def fixbank(self, ctx):
        db, cursor = await get_db_connection('fixbank') #im too fucking lazy to do these ones
        cursor.execute("SELECT bankAmt, userID FROM USERDATA")
        bankdata = cursor.fetchall()
        for amt in bankdata:
            newamt = round(amt[0], 0)
            await ctx.reply(f'newamt + bankdata[1]')
            cursor.execute("UPDATE USERDATA SET bankAmt = %s WHERE userID = %s", (newamt, amt[1]))
            db.commit()
        cursor.execute("SELECT walletAmt, userID FROM USERDATA")
        bankdata = cursor.fetchall()
        for amt in bankdata:
            newamt = round(amt[0], 0)
            await ctx.reply(f'{newamt} + {bankdata[1]}')
            cursor.execute("UPDATE USERDATA SET walletAmt = %s WHERE userID = %s", (newamt, amt[1]))
            db.commit()

    @commands.command(hidden=True)
    @commands.check(isadmin)
    async def temp(self, ctx):
        await dointerest(ctx)

    @commands.command(aliases=['casino'], hidden=True)
    @commands.check(isadmin)
    async def set_casino_money(self, ctx, amt):
        db, cursor = await get_db_connection('setcasinomoney') #im too fucking lazy to do these ones
        cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = %s", (int(amt),))
        db.commit()
        await ctx.reply("okay")

    @commands.command(hidden=True)
    @commands.check(isadmin)
    async def givebotrights(self, ctx):
        db, cursor = await get_db_connection('givebotrights') #im too fucking lazy to do these ones
        cursor.execute("INSERT INTO USERDATA(userID, walletAmt, bankAmt, bankMax, boughtItems, currentXP, userLevel) VALUES (%s, %s, %s, %s, %s, %s, %s)",(self.bot.user.id, 0, 0, 1000, "", 0, 1))
        db.commit()

    @commands.command(hidden=True)
    @commands.check(isadmin)
    async def adduser(self, ctx, userID):
        db, cursor = await get_db_connection('adduser') #im too fucking lazy to do these ones
        if userID is None or type(userID) == int:
            await ctx.reply("You need to enter a userID to add.")
            return
        cursor.execute("INSERT INTO USERDATA(userID, walletAmt, bankAmt, bankMax, boughtItems, currentXP, userLevel) VALUES (%s, %s, %s, %s, %s, %s, %s)", (ctx.author.id, 0, 0, 1000, "", 0, 1))
        db.commit()
        await ctx.reply(f"Added {userID} to the Database \n -# **THERE ARE NO CHECKS TO ENSURE THAT USERID IS VALID!!!!**")

    @commands.command(hidden=True)
    @commands.check(isadmin)
    async def ban(self, ctx, userid):
        db, cursor = await get_db_connection("banuser")
        try:
            user: discord.User = await commands.UserConverter().convert(ctx, userid)
        except commands.CommandError:
            await ctx.reply("Could not find the specified user.")
            return
        cursor.execute("INSERT INTO BANNEDUSERS(userID) VALUES (%s)", (userid,))
        config.banned_users_cache.append(int(userid))
        await ctx.reply(f"Okay i might of banned {user.display_name} lol")

    @commands.command(hidden=True)
    @commands.check(isadmin)
    async def unban(self, ctx, userid):
        db, cursor = await get_db_connection("banuser")
        try:
            user: discord.User = await commands.UserConverter().convert(ctx, userid)
        except commands.CommandError:
            await ctx.reply("Could not find the specified user.")
            return
        cursor.execute("DELETE FROM BANNEDUSERS WHERE userID = %s", (userid,))
        config.banned_users_cache.remove(int(userid))
        await ctx.reply(f"Okay i probably unbanned {user.display_name} lol")

    @commands.command(Hidden=True)
    @commands.check(isadmin)
    async def banlist(self, ctx):
        await ctx.reply(config.banned_users_cache)


    @commands.command(Hidden=True)
    @commands.check(isadmin)
    async def reload(self, ctx, *, cogname):
        if cogname.endswith(".py"):
            cogname = cogname[:-3]
        await self.bot.reload_extension(f"cogs.{cogname}")
        embed = discord.Embed(description=f"**Reload:** Reloaded Cog: `{cogname}.py`", color=discord.Color.blue())
        await ctx.reply(embed=embed)
        print(f"Reloaded Cog: {cogname}.py")

    @commands.command(Hidden=True)
    @commands.check(isadmin)
    async def load(self, ctx, *, cogname):
        if cogname.endswith(".py"):
            cogname = cogname[:-3]
        await self.bot.load_extension(f"cogs.{cogname}")
        embed = discord.Embed(description=f"**Load:** Loaded Cog: `{cogname}.py`", color=discord.Color.blue())
        await ctx.reply(embed=embed)
        print(f"Loaded Cog: {cogname}.py")

    @commands.command(Hidden=True)
    @commands.check(isadmin)
    async def unload(self, ctx, *, cogname):
        if cogname.endswith(".py"):
            cogname = cogname[:-3]
        await self.bot.unload_extension(f"cogs.{cogname}")
        embed = discord.Embed(description=f"**Unload:** Unloaded Cog: `{cogname}.py`", color=discord.Color.blue())
        await ctx.reply(embed=embed)
        print(f"Unloaded Cog: {cogname}.py")


    @commands.command(Hidden=True)
    @commands.check(isadmin)
    async def lock(self, ctx: discord.ext.commands.Context):
        permission: discord.Permissions = ctx.channel.permissions_for(ctx.guild.default_role)
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)

        if permission.send_messages: # currently unlocked, make lockedd
            setattr(overwrite, 'send_messages', False)
            await ctx.message.add_reaction('🔒')
        else: # currently locked (or erroed) make unlocked
            setattr(overwrite, 'send_messages', True)
            await ctx.message.add_reaction('🔓')
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    @commands.command(Hidden=True)
    @commands.check(isadmin)
    async def fw(self, ctx, userid):
        view_items = {
            'serverMute': Button(label="Not in VC", style=discord.ButtonStyle.gray, custom_id="Error!", disabled=True),
            'serverDeafen': Button(label="Not in VC", style=discord.ButtonStyle.gray, custom_id="Error!", disabled=True),
            'disconnect': Button(label="Disconnect", style=discord.ButtonStyle.red, custom_id="disconnect")
            }
        # data to show irrelevant if victim vcing
        member: discord.Member = await ctx.guild.fetch_member(userid)
        userPing = member
        userNick = member.nick
        userRoles: list = member.roles
        userRoles.pop(0)
        role_names = [role.mention for role in userRoles]  # Extract role names
        formatted_roles = ", ".join(role_names)
        if member.avatar.url is not None:
            userThumbnail = member.avatar.url
        #i have to like reconstruct views that's really stupid

        # button callback functions
        async def changeMuteState(interaction: discord.Interaction):
            try:
                if not member.voice.mute:
                    await member.edit(mute=True)
                    view_items['serverMute'].label = "Server Unmute"
                    view_items['serverMute'].style = discord.ButtonStyle.green
                else:
                    await member.edit(mute=False)
                    view_items['serverMute'].label = "Server Mute"
                    view_items['serverMute'].style = discord.ButtonStyle.red
                await interaction.message.edit(view=await createView(view_items))
                await interaction.response.defer()
            except:
                await ctx.reply("I DONT HAVE RIGHTS")
        async def disconnectUser(interaction: discord.Interaction):
            try:
                await member.move_to(None)
                await interaction.response.defer()
            except:
                await ctx.reply("I DONT HAVE RIGHTS")
        async def changeDeafenState(interaction: discord.Interaction):
            try:
                if not member.voice.deaf:
                    await member.edit(deafen=True)
                    view_items['serverDeafen'].label = "Server Undeafen"
                    view_items['serverDeafen'].style = discord.ButtonStyle.green
                else:
                    await member.edit(deafen=False)
                    view_items['serverDeafen'].label = "Server Deafen"
                    view_items['serverDeafen'].style = discord.ButtonStyle.red
                await interaction.message.edit(view=await createView(view_items))
                await interaction.response.defer()
            except:
                await ctx.reply("I DONT HAVE RIGHTS")



        # except if victim not vcing
        try:
            userCurrentChannel = member.voice.channel.id
        except:
            embed = discord.Embed(title=f"{userPing} ({userNick})",description=f"User not in Voice Chat\n\nRoles:\n{formatted_roles}",colour=0x00b0f4, timestamp=datetime.datetime.now())
            embed.set_footer(text=config.STATIC_CREDITS)
            embed.set_thumbnail(url=f"{userThumbnail}")
            await ctx.reply(embed=embed)
            return

        #victim in vc data
        if not member.voice.mute:
            view_items['serverMute'] = Button(label="Server Mute", style=discord.ButtonStyle.red, custom_id="servermute")
        if member.voice.mute:
            userMuted = "Server Muted"
            view_items['serverMute'] = Button(label="Server Unmute", style=discord.ButtonStyle.green, custom_id="serverunmute")
        elif member.voice.self_mute:
            userMuted = "Muted"
        elif not member.voice.self_mute:
            userMuted = "Unmuted"
        else:
            userMuted = "Error"
        if not member.voice.deaf:
            view_items['serverDeafen'] = Button(label="Server Deafen", style=discord.ButtonStyle.red, custom_id="serverdeafen")
        if member.voice.deaf:
            userDeafened = "Server Deafened"
            view_items['serverDeafen'] = Button(label="Server Undeafen", style=discord.ButtonStyle.green, custom_id="serverundeafen")
        elif member.voice.self_deaf:
            userDeafened = "Deafened"
        elif not member.voice.self_deaf:
            userDeafened = "Undeafened"
        else:
            userDeafened = "Error"

        embed = discord.Embed(title=f"{userPing} ({userNick})",description=f"Voice Chat State: {userMuted}, {userDeafened}\nVoice Channel: <#{userCurrentChannel}>\nRoles:\n{formatted_roles}",colour=0x00b0f4,timestamp=datetime.datetime.now())
        embed.set_footer(text=config.STATIC_CREDITS)
        embed.set_thumbnail(url=f"{userThumbnail}")

        view = View()

        for i in view_items.values():
            view.add_item(i)
        view_items['serverDeafen'].callback = changeDeafenState
        view_items['disconnect'].callback = disconnectUser
        view_items['serverMute'].callback = changeMuteState
        await ctx.reply(embed=embed, view=view)
    @commands.command()
    async def remindme(self, ctx, time: str, *, message):
        """
        okay so i think im going to store these as a dictionary being userID: ['time', 'content', 'channel']
        i guess i gotta figure out how to do one of those forever tasks
        lotta fuckin cpu usage though..?
        gotta store in a cache!
        load up: load all reminders into pre said dict
        when new reminder created add to the cache AND the db
        crash ??? idk should be fine i guess since no data should be saved only in the cache
        if time goes delete from cache and db
        on ready: check if any reminders happened when it was offline to avoid bot just forgoring
        """
        time = time.replace("<", "")
        time = time.replace("<", "")
        time = time.replace("t", "")
        time = time.replace(":", "")
        await ctx.reply(time)
        try:
            timeNum: int = int(time)
        except:
            await ctx.reply(f"Please enter a timestamp (number) u silly ")
            return
        db, cursor = await get_db_connection(f'remindme,,')
        cursor.execute("SELECT ReminderCount FROM GLOBALVARIABLES")
        globalCount = cursor.fetchone()
        cursor.execute("UPDATE GLOBALVARIABLES SET ReminderCount = ReminderCount + 1")
        db.commit()
        await ctx.reply(f'{globalCount}: New reminder set for <t:{timeNum}> "{message}"')




async def setup(bot):
    await bot.add_cog(admincommands(bot))
    pass
