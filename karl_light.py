import discord as dc
from discord.ext import commands
import ugame.ugame_cog as ucog

intents = dc.Intents.default()
intents.message_content = True
bot = commands.Bot("~", intents=intents)

with open("ADMINID.txt", "r", encoding="utf-8") as file:
    ADMINID = int(file.readlines()[0])

with open("TOKEN.txt", "r", encoding="utf-8") as file:
    TOKEN = file.readlines()[0]

@bot.event
async def setup_hook():
    '''
    hook up cogs
    '''
    await bot.add_cog(ucog.UgameCommands(bot))

bot.run(TOKEN)
