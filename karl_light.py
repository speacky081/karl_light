import discord as dc
from discord.ext import commands
import ugame.ugame_cog as ucog
import whisper_cog as wcog

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
    await bot.add_cog(wcog.WhisperCog(bot))

@bot.command("sync", help="sync slash commands")
async def sync(ctx: commands.Context):
    '''syncs slash commands'''
    if ctx.author.id == ADMINID:
        await bot.tree.sync()
        await ctx.send('Synced successfully.', ephemeral=True)
    else:
        await ctx.send('You are not the owner.', ephemeral=True)

bot.run(TOKEN)
