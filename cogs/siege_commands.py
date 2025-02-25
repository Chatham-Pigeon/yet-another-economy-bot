import datetime
from gc import enable

from discord.ext import commands
import discord

from siegeapi import Auth
import asyncio

from DISCORD_TOKEN import UBI_PW, UBI_EMAIL
from config import STATIC_CREDITS


class siege_commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def r6stats(self, ctx, user: str):
        auth = Auth(UBI_EMAIL, UBI_PW)
        player = await auth.get_player(name=f"{user}")
        await player.load_persona()
        await player.load_playtime()
        await player.load_ranked_v2()
        await player.load_progress()
        # await player.load_maps() broken
        #await player.load_summaries() broken
        #await player.load_trends() broken
        #await player.load_weapons() broken
        #await player.load_operators() broken
        # await player.load_skill_records() broken
        #await player.load_linked_accounts() broke
        enabled = ""
        if player.persona.enabled is False:
            enabled = "(Disabled)"
        embed = discord.Embed(title=f"{player.name}",
                              description=f"Streamer Nick: {player.persona.nickname} {enabled}\nTotal Playtime: {player.total_time_played_hours:,}h \n PvE Playtme: {round(player.pve_time_played / 60 / 60)}h \n PvP Playtime: {round(player.pvp_time_played / 60/ 60)}h ",
                              colour=0x00b0f4,
                              timestamp=datetime.datetime.now())
        embed.set_author(name="Siege Stats")

        embed.add_field(name="Level Information",
                        value=f"Level: {player.level} \n XP: {player.xp} \n Total XP: {player.total_xp}\nXP to level up: {player.xp_to_level_up}",
                        inline=False)
        embed.add_field(name="Rank (This season)",
                        value=f"Ranked Points: {player.ranked_profile.rank_points}\nRank: {player.ranked_profile.rank}\nPeak Rank Points: {player.ranked_profile.max_rank_points}\nPeak Rank: {player.ranked_profile.max_rank}",
                        inline=False)
        embed.add_field(name=f"{player.ranked_profile.season_code} Stats",
                        value=f"Kills: {player.ranked_profile.kills} \n Deaths: {player.ranked_profile.deaths} \n KDR: {round(player.ranked_profile.kills / player.ranked_profile.deaths, 2)} \n Wins: {player.ranked_profile.wins} \n Losses: {player.ranked_profile.losses} \n WLR: {round(player.ranked_profile.wins / player.ranked_profile.losses, 2)} \n Abandons: {player.ranked_profile.abandons} \n")
        embed.add_field(name="Misc", value=f"{player.casual_profile}")
        embed.set_thumbnail(url=f"{player.profile_pic_url}")
        embed.set_footer(text=f"{STATIC_CREDITS}")
        await ctx.reply(embed=embed)
        await auth.close()

async def setup(bot):
    await bot.add_cog(siege_commands(bot))