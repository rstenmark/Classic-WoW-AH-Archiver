#!/usr/bin/python3

import discord
from discord.ext import commands
from query import get_historical_df

bot = commands.Bot(command_prefix="!")


def to_gold(copper: int) -> float: return round((copper/100)/100, 3)

@bot.command(name='pc')
async def price_check(ctx, *, arg):
    # Keyword only arguments
    # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#keyword-only-arguments
    try:
        df = get_historical_df(arg)
    except IndexError as e:
        await ctx.send("Couldn't find that item.")
        return

    df.market_value = to_gold(df.market_value)
    df.historical_value = to_gold(df.historical_value)
    df.min_buyout = to_gold(df.min_buyout)
    await ctx.send("```" + df.tail(5).to_markdown() + "```")

@bot.event
async def on_ready():
    print('[login] Logged in as {0.user}'.format(bot))

bot.run('[discord bot token here]')
