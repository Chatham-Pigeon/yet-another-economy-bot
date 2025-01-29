import random

import discord
from discord.ext import commands
from discord.ext.commands import BucketType
from discord.ui import Button, View

import config
from helperfunctions import user_data, update_user_data


class moneygaincommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Earns you some money \n30 Second cooldown.")
    @commands.cooldown(1, 30, BucketType.user)
    async def work(self, ctx):
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
                await interaction.response.edit_message(content=f"Good Work! You earned {coinsEarned} coins at your job.",
                                                        view=None)
                userdata['walletAmt'] = userdata["walletAmt"] + coinsEarned
                await update_user_data(userdata, 'work')
            else:
                await interaction.response.edit_message(
                    content=f"Dude what? How'd you fuck that up. The customer left and your employer hates you. \nYou earned no money for this shift.",
                    view=None)

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

    @commands.command(help="Look around for coins on the ground...")
    @commands.cooldown(1, 15, BucketType.user)
    async def search(self, ctx):
        userdata = await user_data(ctx.author.id, 'search')
        if not userdata:
            await ctx.reply("User data not found.")
            return
        rnum = random.randint(1, 100)
        if rnum <= 50:  # sucess
            coinsFound = random.randint(15, 30)
            await ctx.reply(f"You found {coinsFound} coins on the ground!")
            userdata['walletAmt'] = userdata['walletAmt'] + coinsFound

        elif rnum <= 84:  # fail dont lose money
            await ctx.reply("You didn't manage to find anything..")

        elif rnum <= 99:  # fail lose money
            coinsLost = random.randint(15, 30)
            await ctx.reply(f"You ended up losing {coinsLost} coins while searching.. ")
            userdata['walletAmt'] = userdata['walletAmt'] - coinsLost
        elif rnum == 100:
            await ctx.reply(
                f"You searched a bit too hard and fell into the sewers under your bank. The police found you and confiscated half your money.")
            userdata['walletAmt'] = userdata['walletAmt'] / 2
        await update_user_data(userdata, 'search')

    @commands.command(help="Commit Crimes for money")
    @commands.cooldown(1, 90, BucketType.user)
    async def crime(self, ctx):
        messagevalue = config.CRIME_MESSAGES.pop(random.randint(0, len(config.CRIME_MESSAGES) - 1))
        if messagevalue is None:
            messagevalue = "Give me your coins **now**!"
        await ctx.reply(
            f"You want to commit a crime huh? okay then, send \n`{messagevalue}` in chat to try commit a crime.")
        config.user_crime_command[ctx.author.id] = messagevalue



async def setup(bot):
    await bot.add_cog(moneygaincommands(bot))
    pass