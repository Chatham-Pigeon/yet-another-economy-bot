import datetime
import discord
from discord.ext import commands
from discord.ext.commands import BucketType
import random
from discord.ui import Button, View

import config
from helperfunctions import get_db_connection, user_data, update_user_data, user_items, update_user_items, isadmin


async def get_casino_money():
    db, cursor = await get_db_connection('get_casino_money')
    cursor.execute("SELECT casinoPot FROM GLOBALVARIABLES")
    data = cursor.fetchall()
    return 100000 # disable casino Money feature


class moneycommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Rob the specified user, \n However, be careful it could backfire! \n2 Minute cooldown.")
    @commands.cooldown(1, 120, BucketType.user)
    async def rob(self, ctx, user):
        # grab the discord user to rob, if user is none tell them their stupid
        if user:
            try:
                victim = await commands.UserConverter().convert(ctx, user)
            except commands.CommandError:
                await ctx.reply("No user found, try @mention them.")
                self.rob.reset_cooldown(ctx)
                return
        else:
            await ctx.reply("You need to enter a user to rob.")
            self.rob.reset_cooldown(ctx)
            return

        userdata = await user_data(ctx.author.id, 'rob robber')
        useritems = await user_items(ctx.author.id, 'rob user items')

        if not userdata:
            await ctx.reply("Your user data not found.")
            self.rob.reset_cooldown(ctx)
            return

        victimuserdata = await user_data(victim.id, 'rob victim')
        if not userdata:
            await ctx.reply("Victim's user data not found.")
            self.rob.reset_cooldown(ctx)
            return

        if not useritems.__contains__("gun"):
            await ctx.reply("Hey! no one is scared enough of you for that to work... Maybe you should purchase a gun.")
            self.rob.reset_cooldown(ctx)
            return
        if not userdata['walletAmt'] >= 25:
            await ctx.reply("You need atleast 25 coins to rob someone...")
            self.rob.reset_cooldown(ctx)
            return

        if random.randint(1, 100) <= 50:  # success
            coinsStolen = random.randint(1, userdata['walletAmt'])
            userdata['walletAmt'] = userdata['walletAmt'] + coinsStolen
            victimuserdata['walletAmt'] = victimuserdata['walletAmt'] - coinsStolen
            await ctx.reply(
                f"Good Job! {victim.name} was so scared of your gun they dropped {coinsStolen} coins and ran away!")
        else:
            # fail
            coinsStolen = random.randint(1, userdata['walletAmt'] / 4)
            userdata['walletAmt'] = userdata['walletAmt'] - coinsStolen
            victimuserdata['walletAmt'] = victimuserdata['walletAmt'] + coinsStolen
            useritems.remove('gun')
            await ctx.reply(
                f"You failed to rob them and shot yourself in the face... They stole {coinsStolen} coins from your wallet while you were unconscious.")
        await update_user_data(userdata, 'rob user update')
        await update_user_data(victimuserdata, 'rob victim update')
        await update_user_items(useritems, 'rob lose item ')

    @commands.command(aliases=['bal', 'bank', 'wallet'], help="Displays specified users wallet & bank.")
    async def balance(self, ctx, user=None):
        if user:
            try:
                user = await commands.UserConverter().convert(ctx, user)
            except commands.CommandError:
                await ctx.reply("Could not find the specified user.")
                return
        else:
            user = ctx.author
        userdata = await user_data(user.id, 'balance')
        if not userdata:
            await ctx.reply(f"No data found for {user.display_name}.")
            return

        embed = discord.Embed(title=f"{user.display_name}'s Bank Balance",
                              description=f"Wallet: {userdata['walletAmt']}\nBank: {userdata['bankAmt']}/{userdata['bankMax']}",
                              colour=0x00b0f4,
                              timestamp=datetime.datetime.now())
        embed.set_footer(text=f"{config.STATIC_CREDITS}")
        await ctx.reply(embed=embed)


    @commands.command(aliases=['dep'], help="Deposits the specified amount into your bank.")
    async def deposit(self, ctx, depositamt):
        userdata = await user_data(ctx.author.id, 'deposit')
        if not userdata:
            await ctx.reply("User data not found.")
            return

        if depositamt.lower() == "all":
            depositamt = userdata['walletAmt']
        else:
            try:
                depositamt = int(depositamt)
            except ValueError:
                await ctx.reply("Please enter a valid amount or 'all'.")
                return
        if depositamt <= 0:
            await ctx.reply("You cannot deposit zero or negative amounts!")
            return
        if depositamt > userdata['walletAmt']:
            await ctx.reply("You don't have enough coins in your wallet to deposit that amount!")
            return
        if depositamt + userdata['bankAmt'] > userdata['bankMax']:
            space_left = userdata['bankMax'] - userdata['bankAmt']
            await ctx.reply(f"Your bank cannot hold that much! You can only deposit up to {space_left} coins.")
            return

        # Perform the deposit
        userdata['bankAmt'] = userdata['bankAmt'] + depositamt
        userdata['walletAmt'] = userdata['walletAmt'] - depositamt
        await update_user_data(userdata)
        await ctx.reply(f"You have successfully deposited {depositamt} coins into your bank!")

    @commands.command(aliases=['with'], help="Withdraws the specified amount from your bank.")
    async def withdraw(self, ctx, amt):
        userdata = await user_data(ctx.author.id, 'withdraw')
        if not userdata:
            await ctx.reply("User data not found.")
            return

        if amt.lower() == "all":
            amt = userdata['bankAmt']
        else:
            try:
                amt = int(amt)
            except ValueError:
                await ctx.reply("Please enter a valid amount or 'all'.")
                return
        amt = round(amt, 0)
        if amt <= 0:
            await ctx.reply("You cannot withdraw zero or negative amounts!")
            return
        if amt > userdata['bankAmt']:
            await ctx.reply("You don't have enough coins in your bank to withdraw that amount!")
            return

        userdata['walletAmt'] = userdata['walletAmt'] + amt
        userdata['bankAmt'] = userdata['bankAmt'] - amt
        await update_user_data(userdata)
        await ctx.reply(f"You have successfully withdrawn {amt} coins from your bank!")

    @commands.command(aliases=['cf'], help="Gamble away! \n 10% House advantage. \n -# AGPDB Is not at fault for any losses for gambling. Gamble responsibly. ")
    @commands.cooldown(1, 45, BucketType.user)
    async def coinflip(self, ctx, betamt):
        userdata = await user_data(ctx.author.id, 'coinflip')
        if not userdata:
            await ctx.reply("User data not found.")
            return

        try:
            betamt = int(betamt)
        except ValueError:
            await ctx.reply("Enter a number.")
            self.coinflip.reset_cooldown(ctx)
            return
        if betamt < 50:
            await ctx.reply("You need to bet atleast 50 coins.")
            self.coinflip.reset_cooldown(ctx)
            return
        casinoMoney = await get_casino_money()
        if casinoMoney < betamt:
            await ctx.reply(f"The casino isn't rich enough for this bet. They only have {casinoMoney} coins.")
            self.coinflip.reset_cooldown(ctx)
            return
        if userdata['walletAmt'] < betamt:
            await ctx.reply("You don't have enough coins in your wallet for this bet.")
            return

        randomnum = random.randint(1, 100)
        winChance = 50
        if casinoMoney < 200:
            winChance = 25

        db, cursor = await get_db_connection('coinflip')  # EXCLUIVELY FOR THE USE OF CASINOPOT
        if randomnum < winChance: # win
            userdata['walletAmt'] = userdata['walletAmt'] + betamt / 4
            cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot - %s", (betamt / 4,))
            await ctx.reply(f"You won {betamt / 4} coins!")
        else: # lose
            userdata['walletAmt'] = userdata['walletAmt'] - betamt
            cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot + %s", (betamt,))
            await ctx.reply(f"You lost {betamt} coins!")
        db.commit()
        await update_user_data(userdata, 'coinflip game end')

    @commands.command(aliases=['bj'], help="Play a game of Blackjack!")
    @commands.cooldown(1, 30, BucketType.user)
    async def blackjack(self, ctx, betamt: int):
        userdata = await user_data(ctx.author.id, 'coinflip')
        if not userdata:
            await ctx.reply("User data not found.")
            return
        if betamt <= 0:
            await ctx.reply("Please bet a positive amount!")
            self.blackjack.reset_cooldown(ctx)
            return
        if betamt < 50:
            await ctx.reply("You need to bet atleast 50 coins.")
            self.coinflip.reset_cooldown(ctx)
            return
        casinoMoney = await get_casino_money()
        if casinoMoney < betamt:
            await ctx.reply(f"The casino isn't rich enough for this bet. They only have {casinoMoney} coins.")
            self.blackjack.reset_cooldown(ctx)
            return

        # Fetch user data
        if userdata['walletAmt'] < betamt:
            await ctx.reply("You don't have enough coins in your wallet for this bet.")
            self.blackjack.reset_cooldown(ctx)
            return
        userdata['walletAmt'] = userdata['walletAmt'] - betamt
        await update_user_data(userdata, 'blacjack "escrow" ')

        def calculate_hand_value(hand):
            value = 0
            aces = 0
            for card in hand:
                if card in ['J', 'Q', 'K']:
                    value += 10
                elif card == 'A':
                    aces += 1
                    value += 11
                else:
                    value += card
            while value > 21 and aces:
                value -= 10
                aces -= 1
            return value
        db, cursor = await get_db_connection('blackjack') # EXCLUSIVE USE FOR CASINOPOT
        async def blackjack_game(interaction):
            nonlocal player_hand, dealer_hand, deck
            if interaction.user != ctx.author:
                await interaction.response.send_message("You are not part of this game.", ephemeral=True)
                return
            custom_id = interaction.data["custom_id"]

            if custom_id == "hit":
                temp_value = calculate_hand_value(player_hand)
                if casinoMoney < 200:
                    if temp_value >= 12:
                        fake_deck = [10, 'J', 'Q', 'K',]
                    else:
                        fake_deck = [1, 2, 3, 3,]
                    random.shuffle(fake_deck)
                    player_hand.append(fake_deck.pop())
                else:
                    player_hand.append(deck.pop())
                player_value = calculate_hand_value(player_hand)

                if player_value > 21: # bust
                    await interaction.response.edit_message(
                        content=f"You drew a card. Your hand: {', '.join(map(str, player_hand))} (BUSTED!)",
                        view=None
                    )
                    await ctx.reply("You lost the bet. Be more careful next time!")
                    cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot + %s", (betamt,))
                    db.commit()
                    return

                await interaction.response.edit_message(
                    content=f"You drew a card. Your hand: {', '.join(map(str, player_hand))} (Current value: {player_value})",
                    view=view
                )

            # Player chooses to stand
            elif custom_id == "stand":
                player_value = calculate_hand_value(player_hand)

                while calculate_hand_value(dealer_hand) < 17:
                    dealer_hand.append(deck.pop())

                dealer_value = calculate_hand_value(dealer_hand)
                if dealer_value > 21 or player_value > dealer_value: # dealer bust/ player higher than dealer
                    result = "You won!"
                    userdata['walletAmt'] = userdata['walletAmt'] + betamt * 1.5
                    cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot - %s", (betamt * 1.5,))
                elif player_value < dealer_value: # player under dealer
                    result = "You lost!"
                    cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot + %s", (betamt,))
                else: # equal value or smth wwent wrong lol (doubt)
                    result = "It's a draw!"
                    userdata['walletAmt'] = userdata['walletAmt'] + betamt
                db.commit()
                await update_user_data(userdata, 'blackjack game end ')

                await interaction.response.edit_message(
                    content=f"Game over!\nYour hand: {', '.join(map(str, player_hand))} (Value: {player_value})\nDealer's hand: {', '.join(map(str, dealer_hand))} (Value: {dealer_value})\n{result}",
                    view=None
                )
                return

        # Blackjack Game Setup

        deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K', 'A'] * 4
        random.shuffle(deck)

        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]

        if calculate_hand_value(player_hand) == 21:
            await ctx.reply(f"Blackjack! You won!")
            userdata['walletAmt'] = userdata['walletAmt'] + betamt * 1.5
            cursor.execute("UPDATE GLOBALVARIABLE SET casinoPot = casinoPot - %s", (betamt * 1.5,))
            await update_user_data(userdata, 'blackjack blackjack')
            db.commit()
            return
        hit_button = Button(label="Hit", style=discord.ButtonStyle.green, custom_id="hit")
        stand_button = Button(label="Stand", style=discord.ButtonStyle.red, custom_id="stand")
        view = View()
        view.add_item(hit_button)
        view.add_item(stand_button)
        hit_button.callback = blackjack_game
        stand_button.callback = blackjack_game
        await ctx.reply(
            f"Your hand: {', '.join(map(str, player_hand))} (Value: {calculate_hand_value(player_hand)})\nDealer's hand: {dealer_hand[0]}, ?",
            view=view
        )

    @commands.command(help="Pay another user.")
    async def pay(self, ctx, victim, amt):
        userdata = await user_data(ctx.author.id, 'pay payer')
        if not userdata:
            await ctx.reply("Your user data was not found.")
            return
        try:
            user = await commands.UserConverter().convert(ctx, victim)
        except commands.CommandError:
            await ctx.reply("Could not find the payee.")
            return
        payeeuserdata = await user_data(ctx.author.id, 'pay payee')
        if not userdata:
            await ctx.reply("Payee's user data was not found.")
            return
        try:
            amt = int(amt)
        except ValueError:
            await ctx.reply("Enter a whole number.")
            return
        if amt < 1:
            await ctx.reply("You can't donate less than 1 coin.")
            return

        if userdata['walletAmt'] < amt:
            await ctx.reply("You don't have enough coins in your wallet for that.")
            return
        userdata['walletAmt'] = userdata['walletAmt'] - amt
        payeeuserdata['walletAmt'] = payeeuserdata['walletAmt'] + amt
        await update_user_data(userdata, 'pay payer')
        await update_user_data(payeeuserdata, 'pay payee')
        await ctx.reply(f"You paid {user.display_name} **{amt}** coins!")

    @commands.command(help="Plays a game of mines to earn some money.")
    @commands.cooldown(1, 30, BucketType.user)
    async def mines(self, ctx: discord.ext.commands.Context, betAmt):
        userdata = await user_data(ctx.author.id, 'mines')
        if not userdata:
            await ctx.reply("User data was not found.")
            return
        db, cursor = await get_db_connection('mines')

        async def mines_game(interaction: discord.Interaction):
            nonlocal tiles, revealed, bombs, profit, is_game_over
            if interaction.user != ctx.author:
                await interaction.response.send_message("You are not part of this game.", ephemeral=True)
                return
            if is_game_over:
                await interaction.response.send_message("The game is over. Please start a new one. MINES_GAME", ephemeral=True)


            custom_id = interaction.data["custom_id"]
            index = int(custom_id.replace("tile_", ""))
            if index in revealed:
                await interaction.response.send_message("This tile has already been revealed!", ephemeral=True)
                return

            revealed.add(index)

            if index in bombs: # lost
                is_game_over = True
                await interaction.message.edit(
                    content=f"You clicked a bomb! Game over. You lost your bet of {betAmt} coins.",
                    view=None
                )
                cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot + %s", (betAmt,))
                db.commit()
                return



            if len(revealed) >=  9 - bombsCount:  # All good tiles revealed
                is_game_over = True
                winnings = betAmt * 2
                userdata['walletAmt'] =  userdata['walletAmt'] + winnings + betAmt
                await update_user_data(userdata, 'mines all tiles win')
                print('MEOOW')
                cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot - %s", (winnings + betAmt,))
                db.commit()
                await interaction.message.edit(content=f"Congratulations! You revealed all safe tiles and won {winnings} coins!", view=None)
                return

            profit += 0.1
            tiles[index].label = "✔"
            tiles[index].style = discord.ButtonStyle.green
            tiles[index].disabled = True
            coinsEstimate = betAmt * profit
            await interaction.message.edit(
                content=f"Current Profit Multiplier: {profit:.1f}x, Estimated {coinsEstimate} coins. \n Click a tile or exit any time.",
                view=view
            )
            await interaction.response.defer()

        async def exit_game(interaction: discord.Interaction):
            nonlocal is_game_over
            if interaction.user != ctx.author:
                await interaction.response.send_message("You are not part of this game.", ephemeral=True)
                return

            if is_game_over:
                await interaction.response.send_message("The game is already over. EXIT_GAME", ephemeral=True)
                return

            is_game_over = True
            winnings = betAmt * profit
            userdata['walletAmt'] = userdata['walletAmt'] + winnings + betAmt
            await update_user_data(userdata, 'mines exit win')
            cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot - %s", (winnings,))
            db.commit()
            await interaction.response.defer()
            await interaction.message.edit(content=f"You exited the game early! Your winnings are {winnings:.1f} coins.", view=None)

        try:
            betAmt = int(betAmt)
        except ValueError:
            await ctx.reply("Enter a number suitable for betting.")
            self.mines.reset_cooldown(ctx)
            return

        if betAmt <= 0:
            await ctx.reply("Please bet a positive amount!")
            self.mines.reset_cooldown(ctx)

            return

        if userdata['walletAmt'] < betAmt:
            await ctx.reply("You don't have enough coins in your wallet for this bet.")
            self.mines.reset_cooldown(ctx)
            return

        casinoMoney = await get_casino_money()
        if casinoMoney < betAmt:
            await ctx.reply(f"The casino isn't rich enough for this bet. They only have {casinoMoney} coins.")
            self.mines.reset_cooldown(ctx)
            return

        userdata['walletAmt'] = userdata['walletAmt'] - betAmt
        await update_user_data(userdata, 'mines escrow')

        tiles = [Button(style=discord.ButtonStyle.primary, label="?", custom_id=f"tile_{i}") for i in range(9)]
        exit_button = Button(label="Finish ", style=discord.ButtonStyle.red, custom_id="exit")
        blankTile = [Button(style=discord.ButtonStyle.gray, label="Empty", custom_id=f"blank_{i}") for i in range(12)]
        view = View()
        i = 0
        for tile in tiles:
            view.add_item(tile)
            i = i + 1
            if i == 3 or i == 6 or i == 9:
                if i == 9:
                    view.add_item(exit_button)
                else:
                    thattile = blankTile.pop(0)
                    view.add_item(thattile)
                    thattile.disabled = True
                thattile = blankTile.pop(0)
                view.add_item(thattile)
                thattile.disabled = True

        bombsCount = 1
        if casinoMoney < 200:
            bombsCount = 4
        bombs = set(random.sample(range(9), bombsCount))  # Randomly assign 1 bomb location
        revealed = set()
        profit = 0.0
        is_game_over = False

        for tile in tiles:
            tile.callback = mines_game
        exit_button.callback = exit_game

        await ctx.reply(
            "Welcome to the **Mines** game!\nClick tiles to reveal. Avoid the bombs!\nProfit increases by 0.1x for each safe tile.",
            view=view
        )

    @commands.command()
    async def casinoMoney(self, ctx):
        value = await get_casino_money()
        await ctx.reply(value)


    @commands.command(help="Donates money to the casino.")
    async def donate(self, ctx, amt):
        userdata = await user_data(ctx.author.id, 'donate (to casinoPot)')
        db, cursor = await get_db_connection('donate (to casinoPot)') # EXCLUSIVE FOR USE BY CASINoPOT
        if not userdata:
            await ctx.reply("User data was not found.")
            return
        if type(amt) != int:
            await ctx.reply("You neeed to enter a number.")
            return
        if amt < 1:
            await ctx.reply("You can't donate less than 1 coin.")
            return
        if userdata['walletAmt'] < amt:
            await ctx.reply("You don't have enough coins in your wallet for that donation")
            return
        userdata['walletAmt'] = userdata['walletAmt'] - amt
        cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot + %s", (amt,))
        await update_user_data(userdata, 'casinoPot')
        db.commit()
        await ctx.reply(f"You have donated **{amt}** coins to the casino!")

    @commands.command(help="Vs another user in Rock Paper Scissors!", hidden=True)
    async def rps(self, ctx, user, amt):
        userdata = await user_data(ctx, ['walletAmt'])
        if user_data[0] < amt:
            await ctx.reply("You don't have enough money in your wallet for this.")
            return
        if user:
            try:
                victim = await commands.UserConverter().convert(ctx, user)
            except commands.CommandError:
                await ctx.reply("No user found, try @mention them.")
                return

        async def acceptgame_callback(interaction: discord.Interaction):
                if not interaction.user.id == victim.id:
                    return
                custom_id = interaction.data['custom_id']
                if custom_id == 'no':
                    await interaction.response.edit_message(content=f"Sorry, <@{interaction.user.id}> doesn't want to play Rock Paper Scissors against you.", view=None)
                    return

        yesButton = Button(label="Yes", style=discord.ButtonStyle.green, custom_id="Accept")
        noButton = Button(label="No", style=discord.ButtonStyle.red, custom_id="Decline")
        yesButton.callback = acceptgame_callback
        view = View()
        view.add_item(yesButton)
        view.add_item(noButton)
        await ctx.reply(content=f"Hey <@{user.id}>!, <@{ctx.author.id}> wants to play a game of Rock, Paper, Scissors against you for a bet of {amt}, do you want to?", view=view)



async def setup(bot):
    await bot.add_cog(moneycommands(bot))
