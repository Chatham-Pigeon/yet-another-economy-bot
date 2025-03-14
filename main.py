
import asyncio
import datetime
import random
import traceback
from datetime import timedelta
import time

from DISCORD_TOKEN import DISCORD_TOKEN
import discord
from discord.ext import commands

import config
from helperfunctions import user_data, update_user_data, get_db_connection
from helperfunctions import send_log
from cogs.item_commands import itemcommands

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
useitem = itemcommands(bot)

user_level_xp_cooldown = {}
last_command_time = {}
bot_users_this_session = []


async def triedcrime(ctx):
    userdata = await user_data(ctx.author.id, 'triedcrime')
    if not userdata:
        await ctx.reply("User data not found.")
        return
    del config.user_crime_command[ctx.author.id]
    r = random.randint(1, 1000)
    coinsEarned = random.randint(120, 175)
    if r <= 250:
        await ctx.reply(f"You successfully robbed that old lady... She dropped {coinsEarned} coins though!")
        userdata['walletAmt'] = userdata['walletAmt'] + coinsEarned
    elif r <= 750:
        await ctx.reply("You tried to mug someone, but they ran away too fast....")
    elif r <= 999:
        await ctx.reply(f"As you attempted to pickpocket this guy, you realize he is much stronger than you... HE stole {coinsEarned} coins from you")
        userdata['walletAmt'] = userdata['walletAmt'] - coinsEarned
    elif r == 1000:
        await ctx.reply("BRO YOU TRIED TO ROB AN UNDERCOVER COP \n HE ARRESTED YOU AND YOU LOST HALF UR BANK BALANCE LMFAOO")
        userdata['bankAmt'] = userdata['bankAmt'] / 2
    await update_user_data(userdata, 'triedcrime')

@bot.command(help="Shows this help message.")
async def help(ctx):
    embed = discord.Embed(title="Help", description="Available commands and their usage:", color=discord.Color.blue())
    i = 0
    for command in bot.commands:
        i = i + 1
        if i > 25:
            break
        if not command.hidden:
            embed.add_field(
                name=f"!{command.name} {command.signature}",
                value=command.help or "No description provided.",
                inline=True
            )
    await ctx.send(embed=embed)
@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    if user.id == bot.user.id:
        return
    try:
        message: discord.Message
        intendedreaction, message = config.user_challenge_data[user.id]
        if reaction.message.id == message.id:
            if intendedreaction == reaction.emoji:
                coinsEarned = random.randint(1, 250)
                await message.edit(content=f'Good job! You earned {coinsEarned} for this activity')
                userdata =  await user_data(user.id, 'reaction_add')
                userdata['walletAmt'] =  userdata['walletAmt'] + coinsEarned
                await update_user_data(userdata, 'reaction_add')
                del config.user_challenge_data[user.id]
    except:
        pass


@bot.event
async def on_command_error(ctx, error):
    reaction = False
    if isinstance(error, commands.CommandNotFound):
        await ctx.message.add_reaction("❓")
        reaction = True
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.message.add_reaction("❔")
        reaction = True
    elif isinstance(error, commands.MissingPermissions):
        await ctx.reply("You don't have the required permissions to run this command.", ephemeral=True)
    elif isinstance(error, commands.CommandOnCooldown):
        cooldown = str(round(error.retry_after, 0))[:-2]
        for i in cooldown:
            await ctx.message.add_reaction(config.num_to_emoji[i])
        await ctx.message.add_reaction("🕒")
        reaction = True
    elif isinstance(error, commands.CheckFailure):
        pass
    else:
        await ctx.reply(f"An error occurred: {error}")
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        tb_str = "".join(tb)  # Convert the traceback to a string

        # Log the error with the line number and traceback
        error_message = (
            f"❌ **Error in command `{ctx.command}`:**\n"
            f"```{error}```\n"
            f"**Traceback:**\n"
            f"```{tb_str}```"
        )
        print (error_message)
        # Send the error message to the channel (or log it)
        await ctx.reply(error_message)
    if not reaction:
        await ctx.message.add_reaction("❌")

@bot.event
async def on_command_completion(ctx):
    if ctx.command.cog_name == "admin_commands" or ctx.command.cog_name == "admincommands" or ctx.command.cog_name == "siege_commands" or ctx.command.cog_name == "siegecommands":
        return
    await send_log(ctx, "")
    userdata = await user_data(ctx.author.id, 'command completion')
    if not userdata:
        await ctx.reply("Your user data not found.")
        return

    xpgainCooldown = user_level_xp_cooldown.get(ctx.author.id)
    if xpgainCooldown is None or datetime.datetime.now() > xpgainCooldown + timedelta(seconds=5):
        xpgainCooldown = datetime.datetime.now()
        user_level_xp_cooldown[ctx.author.id] = xpgainCooldown
        xpGain = random.randint(1, 10)
        userdata['currentXP'] = userdata['currentXP'] + xpGain
        if userdata['currentXP'] >= userdata['userLevel'] * 100:
            userdata['userLevel'] = userdata['userLevel'] + 1
            userdata['bankMax'] = 1000 + userdata['userLevel'] * 250
            userdata['currentXP'] = userdata['currentXP'] = 0
            await ctx.reply(f"Congratulations {ctx.author.display_name}! You have reached level {userdata['userLevel'] + 1}!")
        await ctx.message.add_reaction("✨")
        await update_user_data(userdata, 'command completion')

    #if config.DEBUG is True:
        #prev_time = last_command_time.pop(f"{ctx.author.id} {ctx.message.id}")
        #time_difference = time.time() - prev_time
        #time_difference = math.trunc(time_difference * 1000)
        #await ctx.reply(f"Pong! {time_difference}ms")

@bot.command(help="Check your XP and Level")
async def level(ctx):
    userdata = await user_data(ctx.author.id, 'level')
    maxXP = userdata['userLevel'] * 100
    embed = discord.Embed(title=f"{ctx.author.display_name}' s Level Info", description=f"Level {userdata['userLevel']}\nxp: {userdata['currentXP']}/{maxXP}", timestamp=datetime.datetime.now(),)
    embed.set_footer(text=f"{config.STATIC_CREDITS}")
    await ctx.reply(embed=embed)

@bot.command(help="Show unqiue stats about the bot!")
async def botstats(ctx):
    # TODO: finish this lol im a bit silly, database values exist never used, need to begin updating all values.
    db, cursor = await get_db_connection("botstats")
    await ctx.reply("Disabled sorry :(")
    return
    cursor.execute("SELECT walletAmt FROM USERDATA")
    alldata: list = cursor.fetchall()
    uniqueUsersCount = alldata.count()
    embed = discord.Embed(title="Bot Stats",timestamp=datetime.now())

    embed.add_field(name=f"Coins spent on items {coinsSpentOnItems}",
                    value="",
                    inline=False)
    embed.add_field(name=f"Total coins robbed {coinsRobbed}",
                    value="",
                    inline=False)
    embed.add_field(name=f"Total coins gained from gambling {coinsGambling}",
                    value="",
                    inline=False)
    embed.add_field(name=f"Total coins lost from gambling {lostGambling}",
                    value="",
                    inline=False)
    embed.add_field(name=f"Number of unqiue users {uniqueUsersCount}",
                    value="",
                    inline=False)
    embed.add_field(name=f"Total Coins ever created {totalCoins}",
                    value="",
                    inline=False)
    embed.set_footer(text=f"{config.STATIC_CREDITS}")
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.author.id in config.user_crime_command:
        crimereq = config.user_crime_command.get(message.author.id)
        if crimereq == message.content:
            await triedcrime(message)
    await bot.process_commands(message)

@bot.event
async def on_ready():
    await bot.get_channel(config.CHANNEL_AGPDS_BOTCMDS).send(":white_check_mark: Bot Ready!")
    db, cursor = await get_db_connection("on ready")
    cursor.execute("SELECT walletAmt, bankAmt FROM USERDATA")
    alldata = cursor.fetchall()
    totalCoins = 0
    for i in alldata:
        for j in i:
            if j > 0:
                totalCoins = totalCoins + j
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching ,name=f"an economy with {totalCoins} coins!"))
    cursor.execute("CREATE TABLE IF NOT EXISTS BANNEDUSERS(userID BIGINT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS GLOBALVARIABLES(casinoPot INT, allCoinsRobbed INT, TotalSpentOnItems INT, allGamblingCoins INT, allGamblingLost INT, allCoinsCreated INT)")
    db.commit()
    cursor.execute("SELECT * FROM BANNEDUSERS")
    alldata = cursor.fetchall()
    for i in alldata:
        config.banned_users_cache.append(i[0])

    print("Bot ready!")




@bot.check
async def everyCommandCheck(ctx: discord.ext.commands.Context):
    if config.banned_users_cache.__contains__(ctx.author.id):
        raise ("You are banned from the bot!")
    last_command_time[f"{ctx.author.id} {ctx.message.id}"] = time.time()
    if bot_users_this_session.__contains__(ctx.author.id):
        return True
    bot_users_this_session.append(ctx.author.id)
    userdata = await user_data(ctx.author.id, 'everyCommandCheck')
    if not userdata:
        embed = discord.Embed(title="Welcome!", description="Hi! Welcome to a general purpose economy bot,\nAll your data should be initalised :3 have fun! \n -# If you are receiving this message & you believe you already have data please @ chatham_pigeon, your data should be safe")
        await ctx.send(embed=embed)
        # Insert default values for the user
        try:
            db, cursor = await get_db_connection("everycommand check (NEW USER)")
            cursor.execute(
                "INSERT INTO USERDATA(userID, walletAmt, bankAmt, bankMax, boughtItems, currentXP, userLevel) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (ctx.author.id, 0, 0, 1000, "", 0, 1))
            db.commit()
        except Exception as e:
            await ctx.reply(e)
    return True

initial_extensions = ['cogs.money_commands', 'cogs.admin_commands', 'cogs.item_commands', 'cogs.moneygain_commands', 'cogs.api_commands']
async def main():
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            print(f"{extension} loaded successfully.")
        except Exception as e:
            print(f"Failed to load extension {extension}: {e}")
    #cursor.execute("CREATE TABLE IF NOT EXISTS GLOBALVARIABLES(casinoPot INT, allCoinsRobbed INT, TotalSpentOnItems INT, allGamblingCoins INT, allGamblingLost INT, allCoinsCreated INT)")
    #cursor.execute("CREATE TABLE IF NOT EXISTS USERDATA(userID BIGINT, walletAmt INT, bankAmt INT, bankMax INT, boughtItems varchar(255), currentXP INT, userLevel INT)")
    #cursor.execute("CREATE TABLE IF NOT EXISTS SHOPITEMS(displayname varchar(255), itemid varchar(255), cost INT, description varchar(255), emoji varchar(255))")

asyncio.run(main())
config.CONFIG_BOT = bot
bot.run(DISCORD_TOKEN)