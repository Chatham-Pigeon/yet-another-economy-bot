import asyncio
import datetime
import sqlite3
import random
from datetime import timedelta
from os import times
from random import randint

from DISCORD_TOKEN import DISCORD_TOKEN
import discord
from discord.ext import commands, tasks
from discord.ext.commands import BucketType
from discord.ui import Button, View

import config
from helperfunctions import isadmin, SQL_EXECUTE, send_log
from cogs.item_commands import itemcommands
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

db = sqlite3.connect("economy.db")
cursor = db.cursor()
db.execute("CREATE TABLE IF NOT EXISTS GLOBALVARIABLES(casinoPot INT)")
db.execute("CREATE TABLE IF NOT EXISTS USERDATA(userID INT, walletAmt INT, bankAmt INT, bankMax INT, boughtItems STRING, currentXP INT, userLevel INT)")
db.execute("CREATE TABLE IF NOT EXISTS SHOPITEMS(displayname STRING, itemid STRING, cost INT, description STRING, emoji STRING)")
useitem = itemcommands(bot)

user_level_xp_cooldown = {}
user_crime_command = {}

tyrobotTimes = []
for i in range(24):
    (tyrobotTimes.append(datetime.time(hour=i), ))
tyrobotTimes.append(datetime.time(hour=11, minute=15))
print(tyrobotTimes)

@bot.command(help="Earns you some money \n30 Second cooldown.")
@commands.cooldown(1, 30, BucketType.user)
async def work(ctx):
    async def work_callback(interaction):
        if interaction.user != ctx.author:
            await interaction.response.send_message("You are not part of this game.", ephemeral=True)
            return
        custom_id = interaction.data["custom_id"]
        if custom_id == 'sucess':
            coinsEarned = random.randint(30, 90)
            await interaction.response.edit_message(content=f"Good Work! You earned {coinsEarned} at your job.", view=None)
            await SQL_EXECUTE('UPDATE', 'USERDATA', {'walletAmt': f'walletAmt = walletAmt + {coinsEarned}'}, {'userID': f'{ctx.author.id}'} )
            cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt + %s WHERE userID = %s", (coinsEarned, ctx.author.id))
            db.commit()
        else:
            await interaction.response.edit_message(content=f"Dude what? How'd you fuck that up. The customer left and your employer hates you. \nYou earned no money for this shift.", view=None)


    randomStyle = [discord.ButtonStyle.primary, discord.ButtonStyle.primary, discord.ButtonStyle.green]
    random.shuffle(randomStyle)
    right_tile = Button(label="Hi! How can I help you?", style=randomStyle.pop(), custom_id="sucess")
    wrong_tile = Button(label="Hi! How can you help me?", style=randomStyle.pop(), custom_id="fail1")
    wrong_tile2 = Button(label="Hi! How can me help I?", style=randomStyle.pop(), custom_id="fail2")
    buttons = [right_tile, wrong_tile, wrong_tile2]
    random.shuffle(buttons)
    view = View()
    for i in buttons:
        view.add_item(i)
        i.callback = work_callback
    await ctx.reply("Click the correct response to help the customer.", view=view)



@bot.command(help="Look around for coins on the ground...")
@commands.cooldown(1, 15, BucketType.user)
async def search(ctx):
    rnum = random.randint(1, 100)
    if rnum <= 50:
        #sucess
        coinsFound = random.randint(15, 30)
        await ctx.reply(f"You found {coinsFound} coins on the ground!")
        cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt + %s WHERE userID = %s", (coinsFound, ctx.author.id))
        db.commit()
    elif rnum == 100:
        await ctx.reply(f"You searched a bit too hard and fell into the sewers under your bank. The police found you and confiscated half your money.")
        cursor.execute("SELECT walletAmt FROM USERDATA WHERE userID = %s", (ctx.author.id,))
        walletAmt = cursor.fetchone()[0] / 2
        cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt - %s WHERE userID = %s", (walletAmt, ctx.author.id))
        db.commit()
    elif rnum <= 84:
        # fail dont lose money
        await ctx.reply("You didn't manage to find anything..")
    else:
        #fail lose money
        coinsLost = random.randint(15, 30)
        await ctx.reply(f"You ended up losing {coinsLost} coins while searching.. ")
        cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt - %s WHERE userID = %s", (coinsLost, ctx.author.id))
        db.commit()

@bot.command(help="Commit Crimes for money")
@commands.cooldown(1, 90, BucketType.user)
async def crime(ctx):
    messagevalue = config.CRIME_MESSAGES.pop(random.randint(0, len(config.CRIME_MESSAGES) - 1))
    if messagevalue is None:
        messagevalue = "Give me your coins!"
    await ctx.reply(f"You want to commit a crime huh? okay then, send \n`{messagevalue}` in chat to try commit a crime.")
    user_crime_command[ctx.author.id] = messagevalue
async def triedcrime(ctx):
    del user_crime_command[ctx.author.id]
    r = random.randint(1, 100)
    coinsEarned = random.randint(120, 175)
    if 1 <= r <= 25:
        await ctx.reply(f"You sucessfully robbed that old lady, damn... She dropped {coinsEarned} coins though..")
        cursor.execute("UPDATE USERDATA SET walletAmt = walletAMt + %s WHERE userID = %s", (coinsEarned, ctx.author.id))
        db.commit()
    elif 26 <= r <= 75:
        await ctx.reply("You tried to mug someone, but they ran away too fast....")
    elif 76 <= r <= 99:
        await ctx.reply(f"As you attempted to pickpocket this guy, you realize he is much stronger than you... HE stole {coinsEarned} coins from you")
        cursor.execute("UPDATE USERDATA SET walletAmt = walletAMt - %s WHERE userID = %s", (coinsEarned, ctx.author.id))
        db.commit()

    elif r == 100:
        await ctx.reply("BRO YOU TRIED TO ROB AN UNDERCOVER COP \n HE ARRESTED YOU AND YOU LOST HALF UR BANK BALANCE LMFAOO")
        cursor.execute("UPDATE USERDATA SET bankAmt = bankAmt / 2 WHERE userID = ?", (ctx.author.id,))
        db.commit()


@bot.command(help="Rob the specified user, \n However, be careful it could backfire! \n2 Minute cooldown.")
@commands.cooldown(1, 120, BucketType.user)
async def rob(ctx, user):
    # grab the discord user to rob, if user is non tell them their stupid
    if user:
        try:
            victim = await commands.UserConverter().convert(ctx, user)
        except commands.CommandError:
            await ctx.reply("No user found, try @mention them.")
            rob.reset_cooldown(ctx)
            return
    else:
        await ctx.reply("You need to enter a user to rob.")
        rob.reset_cooldown(ctx)
        return

    # grab authors data
    cursor.execute("SELECT walletAmt, boughtItems FROM USERDATA WHERE userID = ?", (ctx.author.id,))
    user_data = cursor.fetchone()
    if not user_data:
        await ctx.reply("User data not found.")
        rob.reset_cooldown(ctx)
        return
    wallet, boughtitems = user_data
    if str(boughtitems).__contains__("gun"):
        if wallet >= 25:
            if random.randint(1, 100) <= 50 or await isadmin(ctx):
                # success
                cursor.execute("SELECT walletAmt FROM USERDATA WHERE userID = ?", (victim.id,))
                victimwallet = cursor.fetchone()[0]
                halfvictimwallet = victimwallet // 2
                coinsStolen = random.randint(1, halfvictimwallet)
                cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt + ? WHERE userID = ?", (coinsStolen, ctx.author.id))
                db.commit()
                cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt - ? WHERE userID = ?", (coinsStolen, victim.id))
                db.commit()
                await ctx.reply(f"Good Job! {victim.name} was so scared of your gun they dropped {coinsStolen} coins and ran away!")
            else:
                #fail
                coinsStolen = random.randint(1, 10)
                cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt - ? WHERE userID = ?", (coinsStolen, ctx.author.id))
                db.commit()
                cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt + ? WHERE userID = ?", (coinsStolen, victim.id))
                db.commit()
                boughtitems = boughtitems.replace("gun", "")
                cursor.execute("UPDATE USERDATA SET boughtItems = ? WHERE userID = ?", (boughtitems, ctx.author.id))
                db.commit()
                await ctx.reply(f"You failed to rob them and shot yourself in the face... They stole {coinsStolen} coins from your wallet while you were unconscious.")
        else:
            await ctx.reply("You need atleast 25 coins to rob someone...")
            rob.reset_cooldown(ctx)

    else:
        await ctx.reply("Hey! no one is scared enough of you for that to work... Maybe you should purchase a gun.")
        rob.reset_cooldown(ctx)


@bot.command(help="Shows this help message.")
async def help(ctx):
    embed = discord.Embed(title="Help", description="Available commands and their usage:", color=discord.Color.blue())
    for command in bot.commands:
        if not command.hidden:  # Skip hidden commands
            # Include command name, signature (parameters), and help description
            embed.add_field(
                name=f"!{command.name} {command.signature}",
                value=command.help or "No description provided.",
                inline=False
            )
    await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    await ctx.message.add_reaction("❌")
    if isinstance(error, commands.CommandNotFound):
        msg = await ctx.reply("Command not found.")
    elif isinstance(error, commands.MissingRequiredArgument):
        msg = await ctx.reply("Missing required argument.")
    elif isinstance(error, commands.MissingPermissions):
        msg = await ctx.reply("You don't have the required permissions to run this command.")
    elif isinstance(error, commands.CommandOnCooldown):
        msg = await ctx.reply(f"This command is on cooldown. Try again in {round(error.retry_after, 1)} seconds.")
    else:
        msg = await ctx.reply(f"An error occurred: {error}")
    await asyncio.sleep(10)
    await ctx.message.delete()
    await msg.delete()

@bot.event
async def on_command_completion(ctx):
    await send_log(ctx, "")
    cdstamp = user_level_xp_cooldown.get(ctx.author.id)
    if cdstamp is None or datetime.datetime.now() > cdstamp + timedelta(seconds=5):
        cdstamp = datetime.datetime.now()
        user_level_xp_cooldown[ctx.author.id] = cdstamp
        xpGain = random.randint(1, 10)
        cursor.execute("SELECT currentXP, userLevel FROM USERDATA WHERE userID = ?", (ctx.author.id,))
        user_data = cursor.fetchone()
        currentXP, userLevel = user_data
        currentXP = currentXP + xpGain
        await ctx.message.add_reaction("✨")
        cursor.execute("UPDATE USERDATA SET currentXP = currentXP + ? WHERE userID = ?", (xpGain, ctx.author.id))
        db.commit()
        if currentXP >= userLevel * 100:
            cursor.execute("UPDATE USERDATA SET userLevel = userLevel + 1 WHERE userID = ?", (ctx.author.id,))
            db.commit()
            await ctx.reply(f"Congratulations {ctx.author.display_name}! You have reached level {userLevel + 1}!")
            cursor.execute("UPDATE USERDATA SET bankMax = bankMax + 1000 WHERE userID = ?", (ctx.author.id,))
            db.commit()
            cursor.execute("UPDATE USERDATA SET currentXP = 0 WHERE userID = ?", (ctx.author.id,))
            db.commit()

@bot.command(help="Check your XP and Level")
async def level(ctx):
    cursor.execute("SELECT currentXP, userLevel FROM USERDATA WHERE userID = ?", (ctx.author.id,))
    user_data = cursor.fetchone()
    currentXP, userlevel = user_data
    maxXP = userlevel * 100
    user = ctx.author.display_name
    embed = discord.Embed(title=f"{user}' s Level Info",
                          description=f"Level {level}\nxp: {currentXP}/{maxXP}",
                          timestamp=datetime.datetime.now(),)

    embed.set_footer(text=f"{config.STATIC_CREDITS}")
    await ctx.reply(embed=embed)

@tasks.loop(time=tyrobotTimes)
async def tyrobotcoins():
    cursor.execute("SELECT tyrobotCount, userID from USERDATA")
    all_data = cursor.fetchall()


@bot.event
async def on_member_update(before, after):
    if not hasattr(config, "ROLE_TIMEOUT["):
        return  # Ensure the role config exists before proceeding

    role_timeout = after.guild.get_role(config.ROLE_TIMEOUT)  # Retrieve the role using its ID
    if role_timeout in after.roles and role_timeout not in before.roles:
        # User just got the ROLE_TIMECOUNT role
        cursor.execute("UPDATE USERDATA SET inTimeout = ? WHERE userID = ?", (True, after.id))
        db.commit()
    elif role_timeout not in after.roles and role_timeout in before.roles:
        # User just lost the ROLE_TIMECOUNT role
        cursor.execute("UPDATE USERDATA SET inTimeout = ? WHERE userID = ?", (False, after.id))
        db.commit()


@bot.event
async def on_member_join(member):
    """
    Event triggered when a member joins the server. Assigns the timeout role
    if their 'inTimeout' field in USERDATA is true.
    """
    if not hasattr(config, "ROLE_TIMEOUT"):
        return  # Ensure the role config exists before proceeding

    role_timeout = member.guild.get_role(config.ROLE_TIMEOUT)  # Retrieve the timeout role using its ID
    cursor.execute("SELECT inTimeout FROM USERDATA WHERE userID = ?", (member.id,))
    user_data = cursor.fetchone()

    if user_data and user_data[0]:  # Check if `inTimeout` is true
        if role_timeout:
            await member.add_roles(role_timeout)
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.author.id in user_crime_command:
        crimereq = user_crime_command.get(message.author.id)
        if crimereq == message.content:
            await triedcrime(message)
    await bot.process_commands(message)



@bot.check
async def initUser(ctx):
    cursor.execute("SELECT * FROM userData WHERE userID = ?", (ctx.author.id,))
    user = cursor.fetchone()
    if not user:
        embed = discord.Embed(title="Welcome!", description="Hi! Welcome to a general purpose economy bot,\nAll your data should be initalised :3 have fun!")
        await ctx.send(embed=embed)
        # Insert default values for the user
        try:
            cursor.execute("INSERT INTO USERDATA(userID, walletAmt, bankAmt, bankMax, boughtItems, currentXP, userLevel) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (ctx.author.id, 0, 0, 1000, "", 0, 1))
            db.commit()
        except Exception as e:
            await ctx.reply(e)
    return True

initial_extensions = ['cogs.money_commands', 'cogs.admin_commands', 'cogs.item_commands']
async def main():
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            print(f"{extension} loaded successfully.")
        except Exception as e:
            print(f"Failed to load extension {extension}: {e}")

asyncio.run(main())
bot.run(DISCORD_TOKEN)
