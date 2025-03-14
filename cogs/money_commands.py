import datetime
from code import interact

import discord
from discord.ext import commands
from discord.ext.commands import BucketType
import random
from discord.ui import Button, View

import config
from helperfunctions import get_db_connection, user_data, update_user_data, user_items, update_user_items, isadmin


async def get_casino_money():
    #db, cursor = await get_db_connection('get_casino_money')
    #cursor.execute("SELECT casinoPot FROM GLOBALVARIABLES")
    #data = cursor.fetchall()
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
            coinsStolen = random.randint(1, victimuserdata['walletAmt'])
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
            victim = await commands.UserConverter().convert(ctx, victim)
        except commands.CommandError:
            await ctx.reply("Could not find the payee.")
            return
        payeeuserdata = await user_data(victim.id, 'pay payee')
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
        await ctx.reply(f"You paid {victim.display_name} **{amt}** coins!")


    @commands.command()
    @commands.cooldown(1, 30, BucketType.user)
    async def mines(self, ctx: discord.ext.commands.Context, amt: int):
        tileIndexs = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        tileIndexsCopy = tileIndexs
        bomb_locations: list = [tileIndexsCopy.pop(random.randint(0, len(tileIndexsCopy) - 1)), tileIndexsCopy.pop(random.randint(0, len(tileIndexsCopy) - 1))]

        # function for interacting when user clicks mines button
        async def mines_interaction(interaction: discord.Interaction):
            nonlocal profit, seen_tiles
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("This isn't your mines game", ephemeral=True)
                return
            tile_id = int(interaction.data['custom_id'][5])
            # true if the user just clicked a bomb
            if tile_id in bomb_locations:
                # disable all the tiles
                for i in tiles:
                    i.disabled = True
                # show which bomb user clicked
                tiles[tile_id].style = discord.ButtonStyle.danger
                # show where bombs are
                tiles[bomb_locations[0]].label = "💣"
                tiles[bomb_locations[1]].label = "💣"
                exit_button.disabled =  True
                await interaction.response.edit_message(content="Game over! You hit a bomb...", view=view)
                return
            profit = profit + amt / 7
            seen_tiles = seen_tiles + 1
            # disable & show clicked tile is safe
            tiles[tile_id].label = "✔"
            tiles[tile_id].style = discord.ButtonStyle.green
            tiles[tile_id].disabled = True
            if seen_tiles >= 7:
                for i in tiles:
                    i.disabled = True
                tiles[bomb_locations[0]].label = "💣"
                tiles[bomb_locations[1]].label = "💣"
                exit_button.disabled = True
                await interaction.response.edit_message(content=f"Game over! You found all the safe tiles. you got an extra {round(profit - 50, 0)} coins!", view=view)
                userdata['walletAmt'] = userdata['walletAmt'] + profit
                await update_user_data(userdata)
                return
            await interaction.response.edit_message(content=f"Click the safe tiles and avoid the bombs! +{round(amt / 7, 2)}~ each safe tile. \n Estimated Profit: {round(profit, 0)}", view=view)


        #function with exiting the game
        async def exit_game_buton(interaction: discord.Interaction):
            # disable every tile & show where the bombs are
            for i in tiles:
                i.disabled = True
                i.style = discord.ButtonStyle.success
            tiles[bomb_locations[0]].label = "💣"
            tiles[bomb_locations[1]].label = "💣"
            exit_button.disabled = True
            await interaction.response.edit_message(content=f"Game over! You exited early and profited an extra {profit - 50} coins.", view=view)
            userdata['walletAmt'] = userdata['walletAmt'] + profit
            await update_user_data(userdata)


        # ACTUAL START OF COMMAND
        # common checks to ensure no sneaky business
        userdata = await user_data(ctx.author.id)
        if not userdata:
            await ctx.reply("Failed to get user data.")
            return
        if amt < 50:
            await ctx.reply("You must bet more than 50 coins.")
        if userdata['walletAmt'] < amt:
            await ctx.reply("You can't afford this bet.")

        # take away users money so they cant play a game, and then spend money before game finishes (escrow sorta thing)
        userdata['walletAmt'] = userdata['walletAmt'] - amt
        await update_user_data(userdata)

        profit = amt
        seen_tiles = 0
        # create all 9 buttons that bombs could be on
        tiles = [Button(style=discord.ButtonStyle.primary, label="?", custom_id=f"tile_{i}") for i in range(9)]
        for i in tiles:
            i.callback = mines_interaction
        # red exit button
        exit_button = Button(label="Finish ", style=discord.ButtonStyle.red, custom_id="exit")
        exit_button.callback = exit_game_buton
        # blank tile to force the grid to be a 3x3 (on desktop, i hate mobile users)
        blank_tile = [Button(style=discord.ButtonStyle.gray, label="Empty", custom_id=f"blank_{i}") for i in range(12)]
        view = View()
        i = 0
        for tile in tiles:
            # add first tile
            view.add_item(tile)
            i = i + 1
            # if button index is 3 6 or 9 ( the side of the 3x3 playable grid)
            #buttons added in this if statement are placed AFTER a grid button is added, meaning the blank tile will be on the 4th (and 5th) index of each row
            if i == 3 or i == 6 or i == 9:
                # if its the bottom one
                if i == 9:
                    # add exit button insidead of bank tile
                    view.add_item(exit_button)
                else:
                    # if its not bottom right add blank time
                    thattile = blank_tile.pop(0)
                    view.add_item(thattile)
                    thattile.disabled = True
                # add another blank tile after that (because max button layout is 5 accross, i want grid to be 3x3)
                thattile = blank_tile.pop(0)
                view.add_item(thattile)
                thattile.disabled = True
        await ctx.reply(f"Welcome to Mines, click the safe tiles and avoid the bombs! +{round(amt / 7, 2)}~ profit each safe tile. \n There are two bombs.", view=view)

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

    @commands.command(help="Check Your standing in the coins leaderboard!", aliases=['lb',])
    async def leaderboard(self, ctx):
        db, cursor = await get_db_connection('leaderboard')
        cursor.execute("SELECT userID, walletAmt, bankAmt from USERDATA")
        alldata = cursor.fetchall()
        embed = discord.Embed(title="AGPEB Coins Leaderboard")
        j = 0
        for i in alldata:
            j = j + 1
            totalMoney = i[1] + i[2]
            user: discord.User = await commands.UserConverter().convert(ctx, str(i[0]))
            embed.add_field(name=f"{j} {user.display_name} ({totalMoney})",
                            value="",
                            inline=False)
            if j > 10:
                break
        await ctx.reply(embed=embed)


    @commands.command(help="Vs another user in Rock Paper Scissors!", hidden=True)
    async def rps(self, ctx: discord.ext.commands.Context, user, amt):
        victimchoice: str = ""
        authorchoice: str = ""
        authordata = await user_data(ctx.author.id, 'rps')
        if authordata['walletAmt'] < int(amt):
            await ctx.reply("You don't have enough money in your wallet for this.")
            return
        try:
            amt = int(amt)
        except ValueError:
            await ctx.reply("Enter a number silly")
            return
        if amt < 1:
            await ctx.reply("You can't donate less than 1 coin.")
            return

        if user:
            try:
                victim: discord.User = await commands.UserConverter().convert(ctx, user)
            except commands.CommandError:
                await ctx.reply("No user found, try @mention them.")
                return
        victimdata  = await user_data(victim.id)
        if victimdata['walletAmt'] < int(amt):
            await ctx.reply("The other person doesn't have enough money for that.")
            return
        async def getwinner(victimschoice: str, authorschoice: str):
            victimschoice.lower()
            authorschoice.lower()
            if victimschoice == authorschoice:
                return "tie"
            if victimschoice == 'rock' and authorschoice == 'scissors':
                return "victim"
            elif victimschoice == 'scissors' and authorschoice == 'paper':
                return 'victim'
            elif victimschoice == 'paper' and authorschoice == 'rock':
                return 'victim'
            else:
                return 'author'

        async def makerpschoice(interaction: discord.Interaction):
            nonlocal victimchoice, authorchoice, victim, ctx, authordata
            custom_id = interaction.data['custom_id']
            if interaction.user.id == victim.id:
                victimchoice = custom_id
            elif interaction.user.id == ctx.author.id:
                authorchoice = custom_id
            else:
                await interaction.response.send_message("You arent part of this game!", ephemeral=True)
                return
            if victimchoice and authorchoice:
                await interaction.response.send_message(f"Okay! You picked **{custom_id}**.", ephemeral=True)
                winner = await getwinner(victimchoice, authorchoice)
                if winner == 'tie':
                    await interaction.followup.edit_message(content="It's a tie!", view=None)
                    return
                elif winner == 'victim':
                    await interaction.followup.edit_message(content=f"<@{victim.id}> Won {amt} coins!")
                    victimdata['walletAmt'] = victimdata['walletAmt'] + amt
                    await update_user_data(victimdata)
                    authordata['walletAmt'] = authordata['walletAmt'] - amt
                    await update_user_data(authordata)
                elif winner == 'author':
                    await interaction.followup.edit_message(content=f"<@{ctx.author.id}> Won {amt} coins!", view=None)
                    authordata['walletAmt'] = authordata['walletAmt'] + amt
                    await update_user_data(authordata)
                    victimdata['walletAmt'] = victimdata['walletAmt'] - amt
                    await update_user_data(victimdata)
                return
            else:
                interaction.response.edit_message(f"Okay! Game on. \n The other player has picked.")

            await interaction.response.send_message(f"Okay! You picked **{custom_id}**, lets wait for the other person to pick too.", ephemeral=True)


        async def acceptgame_callback(interaction: discord.Interaction):
            if not interaction.user.id == victim.id:
                await interaction.response.send_message("You arent the recipient of this game invite", ephemeral=True)
                return
            custom_id = interaction.data['custom_id']
            if custom_id == 'no':
                await interaction.response.edit_message(content=f"Sorry, <@{interaction.user.id}> doesn't want to play Rock Paper Scissors against you.", view=None)
                return
            rockButton = Button(label="🪨", style=discord.ButtonStyle.primary, custom_id="Rock")
            paperButton = Button(label="📝", style=discord.ButtonStyle.primary, custom_id="Paper")
            scissorsButton = Button(label="✂️", style=discord.ButtonStyle.primary, custom_id="Scissors")
            rockButton.callback = makerpschoice
            paperButton.callback = makerpschoice
            scissorsButton.callback = makerpschoice
            view = View()
            view.add_item(rockButton)
            view.add_item(paperButton)
            view.add_item(scissorsButton)

            await interaction.response.edit_message(content=f"Okay! Game on.", view=view)


        yesButton = Button(label="Yes", style=discord.ButtonStyle.success, custom_id="Accept")
        noButton = Button(label="No", style=discord.ButtonStyle.red, custom_id="Decline")
        yesButton.callback = acceptgame_callback
        noButton.callback = acceptgame_callback
        view = View()
        view.add_item(yesButton)
        view.add_item(noButton)
        await ctx.reply(content=f"Hey <@{victim.id}>!, <@{ctx.author.id}> wants to play a game of Rock, Paper, Scissors against you for a bet of {amt} coins, do you want to?", view=view)

async def setup(bot):
    await bot.add_cog(moneycommands(bot))
