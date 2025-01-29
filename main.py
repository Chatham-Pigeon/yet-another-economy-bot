
import asyncio
import datetime
import random
from datetime import timedelta
import time
import math

from DISCORD_TOKEN import DISCORD_TOKEN
import discord
from discord.ext import commands
from discord.ext.commands import BucketType
from discord.ui import Button, View

import config
from helperfunctions import user_data, update_user_data, user_items, update_user_items
from helperfunctions import send_log
from cogs.item_commands import itemcommands
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
useitem = itemcommands(bot)

user_level_xp_cooldown = {}
user_crime_command = {}
last_command_time = {}
bot_users_this_session = []



@bot.command(help="Earns you some money \n30 Second cooldown.")
@commands.cooldown(1, 30, BucketType.user)
async def work(ctx):
    userdata = await user_data(ctx.author.id, 'work')
    if not userdata:
        await ctx.reply("User data not found.")
        return
    async def work_callback(interaction):
        if interaction.user != ctx.author:
            await interaction.response.send_message("You are not part of this game.", ephemeral=True)
            return
        custom_id = interaction.data["custom_id"]
        if custom_id == 'sucess':
            coinsEarned = random.randint(30, 90)
            await interaction.response.edit_message(content=f"Good Work! You earned {coinsEarned} at your job.", view=None)
            userdata['walletAmt'] = userdata["walletAmt"] + coinsEarned
            await update_user_data(userdata, 'work')
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
    userdata = await user_data(ctx.author.id, 'search')
    if not userdata:
        await ctx.reply("User data not found.")
        return
    rnum = random.randint(1, 100)
    if rnum <= 50: #sucess
        coinsFound = random.randint(15, 30)
        await ctx.reply(f"You found {coinsFound} coins on the ground!")
        userdata['walletAmt'] = userdata['walletAmt'] + coinsFound

    elif rnum <= 84: # fail dont lose money
        await ctx.reply("You didn't manage to find anything..")

    elif rnum <= 99:  #fail lose money
        coinsLost = random.randint(15, 30)
        await ctx.reply(f"You ended up losing {coinsLost} coins while searching.. ")
        userdata['walletAmt'] = userdata['walletAmt'] - coinsLost
    elif rnum == 100:
        await ctx.reply(f"You searched a bit too hard and fell into the sewers under your bank. The police found you and confiscated half your money.")
        userdata['walletAmt'] = userdata['walletAmt'] / 2
    await update_user_data(userdata, 'search')


@bot.command(help="Commit Crimes for money")
@commands.cooldown(1, 90, BucketType.user)
async def crime(ctx):
    messagevalue = config.CRIME_MESSAGES.pop(random.randint(0, len(config.CRIME_MESSAGES) - 1))
    if messagevalue is None:
        messagevalue = "Give me your coins **now**!"
    await ctx.reply(f"You want to commit a crime huh? okay then, send \n`{messagevalue}` in chat to try commit a crime.")
    user_crime_command[ctx.author.id] = messagevalue

async def triedcrime(ctx):
    userdata = await user_data(ctx.author.id, 'triedcrime')
    if not userdata:
        await ctx.reply("User data not found.")
        return
    del user_crime_command[ctx.author.id]
    r = random.randint(1, 1000)
    coinsEarned = random.randint(120, 175)
    if r <= 250:
        await ctx.reply(f"You successfully robbed that old lady... She dropped {coinsEarned} coins though!")
        userdata['walletAmt'] = userdata['walletAmt'] + coinsEarned
    elif r <= 750:
        await ctx.reply("You tried to mug someone, but they ran away too fast....")
    elif r <= 999 :
        await ctx.reply(f"As you attempted to pickpocket this guy, you realize he is much stronger than you... HE stole {coinsEarned} coins from you")
        userdata['walletAmt'] = userdata['walletAmt'] - coinsEarned
    elif r == 1000:
        await ctx.reply("BRO YOU TRIED TO ROB AN UNDERCOVER COP \n HE ARRESTED YOU AND YOU LOST HALF UR BANK BALANCE LMFAOO")
        userdata['bankAmt'] = userdata['bankAmt'] / 2
    await update_user_data(userdata, 'triedcrime')

@bot.command(help="Rob the specified user, \n However, be careful it could backfire! \n2 Minute cooldown.")
@commands.cooldown(1, 120, BucketType.user)
async def rob(ctx, user):
    # grab the discord user to rob, if user is none tell them their stupid
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

    userdata = await user_data(ctx.author.id, 'rob robber')
    useritems = await user_items(ctx.author.id, 'rob user items')

    if not userdata:
        await ctx.reply("Your user data not found.")
        rob.reset_cooldown(ctx)
        return

    victimuserdata = await user_data(victim.id, 'rob victim')
    if not userdata:
        await ctx.reply("Victim's user data not found.")
        rob.reset_cooldown(ctx)
        return

    if not useritems.__contains__("gun"):
        await ctx.reply("Hey! no one is scared enough of you for that to work... Maybe you should purchase a gun.")
        rob.reset_cooldown(ctx)
        return
    if not userdata['walletAmt'] >= 25:
        await ctx.reply("You need atleast 25 coins to rob someone...")
        rob.reset_cooldown(ctx)
        return

    if random.randint(1, 100) <= 50: # success
        coinsStolen = random.randint(1, userdata['walletAmt'])
        userdata['walletAmt'] = userdata['walletAmt'] + coinsStolen
        victimuserdata['walletAmt'] = victimuserdata['walletAmt'] - coinsStolen
        await ctx.reply(f"Good Job! {victim.name} was so scared of your gun they dropped {coinsStolen} coins and ran away!")
    else:
        #fail
        coinsStolen = random.randint(1, userdata['walletAmt'] / 4)
        userdata['walletAmt'] = userdata['walletAmt'] - coinsStolen
        victimuserdata['walletAmt'] = victimuserdata['walletAmt'] + coinsStolen
        useritems.remove('gun')
        await ctx.reply(f"You failed to rob them and shot yourself in the face... They stole {coinsStolen} coins from your wallet while you were unconscious.")
    await update_user_data(userdata, 'rob user update')
    await update_user_data(victimuserdata, 'rob victim update')
    await update_user_items(useritems, 'rob lose item ')





@bot.command(help="Shows this help message.")
async def help(ctx):
    embed = discord.Embed(title="Help", description="Available commands and their usage:", color=discord.Color.blue())
    for command in bot.commands:
        if not command.hidden:
            embed.add_field(
                name=f"!{command.name} {command.signature}",
                value=command.help or "No description provided.",
                inline=False
            )
    await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    reaction = False
    if isinstance(error, commands.CommandNotFound):
        await ctx.message.add_reaction("❓")
        reaction = True
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.message.add_reaction("❔")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.reply("You don't have the required permissions to run this command.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"This command is on cooldown. Try again in {round(error.retry_after, 1)} seconds.")
    elif isinstance(error, commands.CheckFailure):
        pass
    else:
        await ctx.reply(f"An error occurred: {error}")
    if not reaction:
        await ctx.message.add_reaction("❌")

@bot.event
async def on_command_completion(ctx):
    if ctx.command.cog_name == "admin_commands" or ctx.command.cog_name == "admincommands":
        return
    await send_log(ctx, "")
    userdata = await user_data(ctx.author.id, 'command completion')
    if not userdata:
        await ctx.reply("Your user data not found.")
        rob.reset_cooldown(ctx)
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
            await update_user_data(userdata, 'command completion')
            await ctx.reply(f"Congratulations {ctx.author.display_name}! You have reached level {userdata['userLevel'] + 1}!")
        await ctx.message.add_reaction("✨")

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


@bot.command(Hidden=True)
async def test(ctx):
    await user_items(ctx.author.id)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.author.id in user_crime_command:
        crimereq = user_crime_command.get(message.author.id)
        if crimereq == message.content:
            await triedcrime(message)
    await bot.process_commands(message)

@bot.event
async def on_ready():
    await bot.get_channel(config.CHANNEL_AGPDS_BOTCMDS).send(":white_check_mark: Bot Ready!")

@bot.check
async def everyCommandCheck(ctx):
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
            userdata = {
                'userID': ctx.author.id,
                'walletAmt': 0,
                'bankAmt': 0,
                'bankMax': 1000,
                'boughtItems': "",
                'currentXP': 0,
                'userLevel': 1
            }
            await update_user_data(userdata, 'everyCommandCheck (NEW USER)')
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
    #cursor.execute("CREATE TABLE IF NOT EXISTS GLOBALVARIABLES(casinoPot INT)")
    #cursor.execute("CREATE TABLE IF NOT EXISTS USERDATA(userID BIGINT, walletAmt INT, bankAmt INT, bankMax INT, boughtItems varchar(255), currentXP INT, userLevel INT)")
    #cursor.execute("CREATE TABLE IF NOT EXISTS SHOPITEMS(displayname varchar(255), itemid varchar(255), cost INT, description varchar(255), emoji varchar(255))")


asyncio.run(main())
config.CONFIG_BOT = bot
bot.run(DISCORD_TOKEN)
