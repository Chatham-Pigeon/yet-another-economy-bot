import asyncio
import datetime

import discord
from discord.ext import commands
from discord.ext.commands import BucketType, CommandOnCooldown
import random
from discord.ui import Button, View

import config
from helperfunctions import isadmin, SQL_EXECUTE, get_db_connection

db= get_db_connection()
cursor = db.cursor()


async def get_casino_money():
    cursor.execute("SELECT casinoPot FROM GLOBALVARIABLES")
    data = cursor.fetchone()
    return data[0]


class moneycommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['bal', 'bank', 'wallet'], help="Displays specified users wallet & bank.")
    async def balance(self, ctx, user=None):
        # Determine whose balance to fetch
        if user:
            try:
                user = await commands.UserConverter().convert(ctx, user)
            except commands.CommandError:
                await ctx.reply("Could not find the specified user.")
                return
        else:
            user = ctx.author

        # Fetch user data
        cursor.execute("SELECT walletAmt, bankAmt, bankMax FROM userData WHERE userID = %s", (user.id,))
        user_data = cursor.fetchone()

        try:
            if not user_data:
                await ctx.reply(f"No data found for {user.display_name}.")
                return

            wallet, bank, bank_max = user_data
            embed = discord.Embed(title=f"{user.display_name}'s Bank Balance",
                                  description=f"Wallet: {wallet}\nBank: {bank}/{bank_max}",
                                  colour=0x00b0f4,
                                  timestamp=datetime.datetime.now())

            embed.set_footer(text=f"{config.STATIC_CREDITS}")
            await ctx.reply(embed=embed)
        except Exception as e:
            await ctx.reply(e)

    @commands.command(aliases=['dep'], help="Deposits the specified amount into your bank.")
    async def deposit(self, ctx, depositamt):
        try:
            # Fetch user data
            cursor.execute("SELECT walletAmt, bankAmt, bankMax FROM USERDATA WHERE userID = %s", (ctx.author.id,))
            user_data = cursor.fetchone()

            if not user_data:
                await ctx.reply("User data not found.")
                return

            wallet, bank, bank_max = user_data

            if depositamt.lower() == "all":
                depositamt = wallet
            else:
                try:
                    depositamt = int(depositamt)
                except ValueError:
                    await ctx.reply("Please enter a valid amount or 'all'.")
                    return

            if depositamt <= 0:
                await ctx.reply("You cannot deposit zero or negative amounts!")
                return

            if depositamt > wallet:
                await ctx.reply("You don't have enough coins in your wallet to deposit that amount!")
                return

            if depositamt + bank > bank_max:
                space_left = bank_max - bank
                await ctx.reply(f"Your bank cannot hold that much! You can only deposit up to {space_left} coins.")
                return

            # Perform the deposit
            cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt - %s, bankAmt = bankAmt + %s WHERE userID = %s",
                           (depositamt, depositamt, ctx.author.id))
            db.commit()
            await ctx.reply(f"You have successfully deposited {depositamt} coins into your bank!")

        except Exception as e:
            await ctx.reply(f"An error occurred: {e}")

    @commands.command(aliases=['with'], help="Withdraws the specified amount from your bank.")
    async def withdraw(self, ctx, amt):
        try:
            # Fetch user data
            cursor.execute("SELECT walletAmt, bankAmt, bankMax FROM USERDATA WHERE userID = %s", (ctx.author.id,))
            user_data = cursor.fetchone()

            if not user_data:
                await ctx.reply("User data not found.")
                return

            wallet, bank, bank_max = user_data

            if amt.lower() == "all":
                amt = bank
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

            if amt > bank:
                await ctx.reply("You don't have enough coins in your bank to withdraw that amount!")
                return

            cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt + %s, bankAmt = bankAmt - %s WHERE userID = %s",
                           (amt, amt, ctx.author.id))
            db.commit()
            await ctx.reply(f"You have successfully withdrawn {amt} coins from your bank!")

        except Exception as e:
            await ctx.reply(f"An error occurred: {e}")

    @commands.command(aliases=['cf'], help="Gamble away! \n 10% House advantage. \n -# AGPDB Is not at fault for any losses for gambling. Gamble responsibly. ")
    @commands.cooldown(1, 45, BucketType.user)
    async def coinflip(self, ctx, betamt):
        try:
            betamt = int(betamt)
        except:
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

        cursor.execute("SELECT walletAmt FROM USERDATA WHERE userID = %s", (ctx.author.id,))
        user_data = cursor.fetchone()
        if user_data[0] < betamt:
            await ctx.reply("You don't have enough coins in your wallet for this bet.")
            return
        randomnum = random.randint(1, 100)
        winChance = 50
        if casinoMoney < 200:
            winChance = 25
        if randomnum < winChance or isadmin(ctx):
            cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt + %s WHERE userID = %s", (betamt / 4, ctx.author.id))
            cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot - %s", (betamt / 4,))
            db.commit()
            await ctx.reply(f"You won {betamt / 4} coins!")
            await self.bot.get_channel(config.CHANNEL_LOG).send(content=f"<@{ctx.author.id}> **won** a bet with a value of `{randomnum}`")
        else:
            cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt - %s WHERE userID = %s", (betamt, ctx.author.id))
            cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot + %s", (betamt,))
            db.commit()
            await ctx.reply(f"You lost {betamt} coins!")
            await self.bot.get_channel(config.CHANNEL_LOG).send(content=f"<@{ctx.author.id}> **lost** a bet with a value of `{randomnum}`")

    @commands.command(aliases=['bj'], help="Play a game of Blackjack!")
    @commands.cooldown(1, 30, BucketType.user)
    async def blackjack(self, ctx, betamt: int):
        if betamt <= 0:
            await ctx.reply("Please bet a positive amount!")
            self.blackjack.reset_cooldown(ctx)

            return
        casinoMoney = await get_casino_money()
        if casinoMoney < betamt:
            await ctx.reply(f"The casino isn't rich enough for this bet. They only have {casinoMoney} coins.")
            self.blackjack.reset_cooldown(ctx)
            return

        # Fetch user data
        cursor.execute("SELECT walletAmt FROM USERDATA WHERE userID = %s", (ctx.author.id,))
        user_data = cursor.fetchone()
        if not user_data or user_data[0] < betamt:
            await ctx.reply("You don't have enough coins in your wallet for this bet.")
            self.blackjack.reset_cooldown(ctx)
            return

        cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt - %s WHERE userID = %s",(betamt, ctx.author.id))
        db.commit()

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

        async def blackjack_game(interaction):
            nonlocal player_hand, dealer_hand, deck

            # Check if user clicked their button
            if interaction.user != ctx.author:
                await interaction.response.send_message("You are not part of this game.", ephemeral=True)
                return
            custom_id = interaction.data["custom_id"]
            # Player chooses to hit
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

                # Check if player busts
                if player_value > 21:
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
                result = None

                if dealer_value > 21 or player_value > dealer_value:
                    result = "You won!"
                    cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt + %s WHERE userID = %s", (betamt * 1.5, ctx.author.id))
                    db.commit()
                    cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot - %s", (betamt * 1.5,))
                    db.commit()
                elif player_value < dealer_value:
                    result = "You lost!"
                    cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot + %s", (betamt,))
                    db.commit()

                else:
                    result = "It's a draw!"
                    cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt + %s WHERE userID = %s", (betamt, ctx.author.id))
                    db.commit()

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
            cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt + %s WHERE userID = %s",
                           (betamt * 1.5, ctx.author.id))
            db.commit()
            cursor.execute("UPDATE GLOBALVARIABLE SET casinoPot = casinoPot - %s", (betamt * 1.5,))
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
        try:
            user = await commands.UserConverter().convert(ctx, victim)
        except commands.CommandError:
            await ctx.reply("Could not find the specified user.")
            return
        try:
            amt = int(amt)
        except:
            await ctx.reply("enter a whole number.")
            return
        if amt < 1:
            await ctx.reply("you can't donate less than 1 coin")
            return

        cursor.execute("SELECT walletAmt FROM USERDATA WHERE userID = %s", (ctx.author.id,))
        user_data = cursor.fetchone()
        if user_data[0] < amt:
            await ctx.reply("you can't give that much ur too poor")
            return
        cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt + %s where userID = %s ", (amt, user.id))
        db.commit()
        cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt - %s where userID = ? ", (amt, ctx.author.id))
        db.commit()
        await ctx.reply(f"You paid {user.display_name} {amt} coins!")

    @commands.command(help="Plays a game of mines to earn some money.")
    @commands.cooldown(1, 30, BucketType.user)
    async def mines(self, ctx, betAmt):

        import random
        from discord.ui import Button, View

        async def mines_game(interaction):
            nonlocal tiles, revealed, bombs, profit, is_game_over
            if interaction.user != ctx.author:
                await interaction.response.send_message("You are not part of this game.", ephemeral=True)
                return

            if is_game_over:
                await interaction.response.send_message("The game is over. Please start a new one.", ephemeral=True)
                return

            custom_id = interaction.data["custom_id"]
            index = int(custom_id.replace("tile_", ""))
            if index in revealed:
                await interaction.response.send_message("This tile has already been revealed!", ephemeral=True)
                return

            revealed.add(index)

            if index in bombs:
                is_game_over = True
                await interaction.response.edit_message(
                    content=f"You clicked a bomb! Game over. You lost your bet of {betAmt} coins.",
                    view=None
                )
                cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot + ?", (betAmt,))
                db.commit()
                return

            profit += 0.2
            tiles[index].label = "✔"
            tiles[index].style = discord.ButtonStyle.green
            tiles[index].disabled = True

            if len(revealed) == 7:  # All good tiles revealed
                is_game_over = True
                winnings = betAmt * 2
                cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt + ? WHERE userID = ?",(winnings + betAmt, ctx.author.id))
                cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot - ?", (winnings + betAmt,))

                await interaction.response.edit_message(
                    content=f"Congratulations! You revealed all safe tiles and won {winnings} coins!",
                    view=None
                )
                return

            await interaction.response.edit_message(
                content=f"Current Profit Multiplier: {profit:.1f}x\nClick a tile or exit any time.",
                view=view
            )

        async def exit_game(interaction):
            nonlocal is_game_over
            if interaction.user != ctx.author:
                await interaction.response.send_message("You are not part of this game.", ephemeral=True)
                return

            if is_game_over:
                await interaction.response.send_message("The game is already over.", ephemeral=True)
                return

            is_game_over = True
            winnings = betAmt * profit
            cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt + ? WHERE userID = ?", (winnings + betAmt, ctx.author.id))
            cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot - ?", (winnings,))
            db.commit()
            await interaction.response.edit_message(
                content=f"You exited the game early! Your winnings are {winnings:.1f} coins.",
                view=None
            )

        try:
            betAmt = int(betAmt)
        except:
            await ctx.reply("Enter a number suitable for betting.")
            self.mines.reset_cooldown(ctx)
            return

        if betAmt <= 0:
            await ctx.reply("Please bet a positive amount!")
            self.mines.reset_cooldown(ctx)

            return

        cursor.execute("SELECT walletAmt FROM USERDATA WHERE userID = ?", (ctx.author.id,))
        user_data = cursor.fetchone()
        if not user_data or user_data[0] < betAmt:
            await ctx.reply("You don't have enough coins in your wallet for this bet.")
            self.mines.reset_cooldown(ctx)

            return
        casinoMoney = await get_casino_money()
        if casinoMoney < betAmt:
            await ctx.reply(f"The casino isn't rich enough for this bet. They only have {casinoMoney} coins.")
            self.mines.reset_cooldown(ctx)
            return

        cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt - ? WHERE userID = ?", (betAmt, ctx.author.id))
        db.commit()

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
        bombs = set(random.sample(range(9), bombsCount))  # Randomly assign 2 bomb locations
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
        if not amt is None:
            cursor.execute("SELECT walletAmt from USERDATA WHERE userID = ? ", (ctx.author.id,))
            user_data = cursor.fetchone()
            if user_data[0] < int(amt):
                await ctx.reply("You don't have enough coins in your wallet for this donation.")
                return
            cursor.execute("UPDATE USERDATA SET walletAmt = walletAmt - ? WHERE userID = ?", (int(amt), ctx.author.id))
            db.commit()
            await ctx.reply(f"You have donated {amt} coins to the casino!")
            cursor.execute("UPDATE GLOBALVARIABLES SET casinoPot = casinoPot + ?", (int(amt),))
            db.commit()

    @commands.command(help="Vs another user in Rock Paper Scissors!", hidden=True)
    async def rps(self, ctx, user, amt):
        # too lazy to continue this too hard :(
        cursor.execute("SELECT walletAmt FROM USERDATA WHERE userID = ?", (ctx.author.id,))
        user_data = cursor.fetchone()
        if user_data[0] < amt:
            await ctx.reply("You don't have enough money in your wallet for this.")
            return
        if user:
            try:
                victim = await commands.UserConverter().convert(ctx, user)
            except commands.CommandError:
                await ctx.reply("No user found, try @mention them.")
                return

        async def acceptgame_callback(interaction):
                custom_id = interaction.data['custom_id']
                if custom_id == 'yes':
                    pass
                else:
                    await interaction.response.edit_message(content=f"Sorry, <@{interaction.user.id}> doesn't want to play Rock Paper Scissors against you.", view=None)
        yesButton = Button(label="Yes", style=discord.ButtonStyle.green, custom_id="Accept")
        noButton = Button(label="No", style=discord.ButtonStyle.red, custom_id="Decline")
        await ctx.reply(f"Hey <@{user.id}>!, <@{ctx.author.id}> wants to play a game of Rock, Paper, Scissors against you for a bet of {amt}, do you want to?")




async def setup(bot):
    await bot.add_cog(moneycommands(bot))
