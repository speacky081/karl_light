import sqlite3
import datetime
import pytz
import discord as dc
from discord.ext import commands, tasks
import ugame.ugame_cog as ucog
import whisper_cog as wcog
import tcg_cog as tcog

intents = dc.Intents.default()
intents.message_content = True
bot = commands.Bot("~", intents=intents)

with open("ADMINID.txt", "r", encoding="utf-8") as file:
    ADMINID = int(file.readlines()[0])

with open("TOKEN.txt", "r", encoding="utf-8") as file:
    TOKEN = file.readlines()[0]

TZ = pytz.timezone('Europe/Berlin')

@bot.event
async def setup_hook():
    '''
    hook up cogs
    '''
    await bot.add_cog(ucog.UgameCommands(bot))
    await bot.add_cog(wcog.WhisperCog(bot))
    await bot.add_cog(tcog.Tcg(bot))
    bot.tree.add_command(wcog.reply_context)

@tasks.loop(time=datetime.time(hour=4, minute=0, tzinfo=TZ))
async def daily_job():
    '''run the daily token method at 4Am'''
    tcog.daily_token()

@daily_job.before_loop
async def before_daily_job():
    '''before the daily job start check if bot is ready'''
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    '''executes when bot is fully up and running'''
    print("❯ Slash commands *loaded* in bot.tree:")
    for cmd in bot.tree.walk_commands():
        print(f"  • {cmd.name} (guild_ids={cmd._guild_ids})")
    global_cmds = await bot.tree.fetch_commands()                   # global
    guild_cmds  = await bot.tree.fetch_commands(guild=dc.Object(id=1163493648462270664))
    print("❯ Global on Discord:", [c.name for c in global_cmds])
    print("❯ Guild‑scoped on Discord:", [c.name for c in guild_cmds])

    if not daily_job.is_running():
        daily_job.start()
    commands_in_guild = await bot.tree.fetch_commands(guild=dc.Object(id=1163493648462270664))
    print("Commands live in guild:", [c.name for c in commands_in_guild])

    # set "playing" to 0 on reboot because I am too stupid
    con = sqlite3.connect("tcg.db")
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tcgames (
        start_time_unix INTEGER,
        playing INTEGER,
        type INTEGER,
        image TEXT
    )
    """)

    # make sure one row exists
    cur.execute("""
    INSERT INTO tcgames (start_time_unix, playing, type, image)
    SELECT 0, 0, 0, ''
    WHERE NOT EXISTS (SELECT 1 FROM tcgames)
    """)

    # now safe to fetch
    cur.execute("UPDATE tcgames SET playing = ?", (0,))

    con.commit()
    con.close()

@bot.command("sync", help="sync slash commands")
async def sync(ctx: commands.Context):
    '''syncs slash commands'''
    if ctx.author.id == ADMINID:
        synced = await bot.tree.sync()
        await ctx.send(f"Synced {len(synced)} commands", ephemeral=True)
    else:
        await ctx.send('You are not the owner.', ephemeral=True)

bot.run(TOKEN)
