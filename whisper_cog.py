import os.path
import discord as dc
from discord import app_commands
from discord.ext import commands

class WhisperCog(dc.ext.commands.Cog):
    '''
    Cog for sending messages anonymously
    '''
    def __init__(self, bot):
        self.bot = bot
        if not os.path.isfile("whisper_clients.txt"):
            with open("whisper_clients.txt", "w", encoding="utf-8") as clients:
                clients.write("")
        with open("whisper_clients.txt", "r", encoding="utf-8") as clients:
            self.clients = [line.strip() for line in clients]

    @commands.Cog.listener()
    async def on_message(self, message: dc.Message):
        '''Listen for non-whisper messages and delete them'''
        if not message.author.bot and message.channel.id == 1397636825971032095:
            if len(message.attachments[0]) > 0:
                attachment_url = message.attachments[0].url
                await message.channel.send(attachment_url)
            await message.channel.send(message.content)
            await message.delete()

    @app_commands.context_menu(name="Antworten")
    async def reply(self, interaction: dc.Interaction, message: dc.Message, reply: str):
        """Enable people to reply-whisper to messages"""
        await interaction.response.defer(ephemeral=True)
        channel = self.bot.get_channel(1397636825971032095)
        if channel is None:
            channel = await self.bot.fetch_channel(1397636825971032095)
        if message.channel.id != 1397636825971032095:
            await interaction.followup.send("Du kannst das nur im anonymous channel machen", ephemeral=True)
            return
        await message.reply(" \n" + "**ANONYM  **" + reply, allowed_mentions = dc.AllowedMentions(everyone=False))

    @app_commands.command(
        name="whisper", description="Sag etwas, aber bleib dabei anonym")
    async def whisper(self, interaction: dc.Interaction, message: str, att: dc.Attachment = None):
        '''so simple it doesn't need a docstring'''
        await interaction.response.defer(ephemeral=True)
        channel = self.bot.get_channel(1397636825971032095)
        if channel is None:
            channel = await self.bot.fetch_channel(1397636825971032095)
        if att is None:
            await channel.send(" \n" + "**ANONYM  **" + message, allowed_mentions = dc.AllowedMentions(everyone=False))
        else:
            file = await att.to_file()
            await channel.send(" \n" + "**ANONYM  **" + message, file=file, allowed_mentions=dc.AllowedMentions(everyone=False))
        with open("whisper_clients.txt", "r", encoding="utf-8") as clients:
            self.clients = [line.strip() for line in clients]
        for client in self.clients:
            channel = await self.bot.fetch_user(int(client))
            if att is None:
                await channel.send(" \n" + "**ANONYM  **" + message, allowed_mentions = dc.AllowedMentions(everyone=False))
            else:
                file = await att.to_file()
                await channel.send(" \n" + "**ANONYM  **" + message, file=file, allowed_mentions = dc.AllowedMentions(everyone=False))
        await interaction.delete_original_response()

    @app_commands.command(
        name="whisper-register",
        description="Lass dir die anonymen Nachrichten per DM zuschicken"
        )
    async def sign_up(self, interaction: dc.Interaction):
        '''register user as client for private messaging'''
        await interaction.response.defer(ephemeral=True)

        with open("whisper_clients.txt", "r", encoding="utf-8") as clients:
            self.clients = [line.strip() for line in clients]

        if str(interaction.user.id) in self.clients:
            await interaction.channel.send("Du bist schon registriert")
        else:
            with open("whisper_clients.txt", "a", encoding="utf-8") as file:
                file.write(str(interaction.user.id) + "\n")
                self.clients.append(str(interaction.user.id))
            await interaction.user.send("Du wurdest für die Nachrichtenweiterleitung registriert")
        await interaction.delete_original_response()

    @app_commands.command(
        name="whisper-deregister",
        description="Lass dir die anonymen Nachrichten nicht mehr per DM schicken"
        )
    async def sign_out(self, interaction: dc.Interaction):
        '''deregister user as client for private messaging'''
        await interaction.response.defer(ephemeral=True)

        with open("whisper_clients.txt", "r", encoding="utf-8") as clients:
            self.clients = [line.strip() for line in clients]

        if str(interaction.user.id) in self.clients:
            # check if client is signed up for message forwarding
            # if so delete them from the register
            with open("whisper_clients.txt", "w", encoding="utf-8") as file:
                for client in self.clients:
                    if client != str(interaction.user.id):
                        file.write(client + "\n")
            await interaction.user.send("Du wurdest von der Nachrichtenweiterleitung abgemeldet")
        else:
            await interaction.followup.send("Du bist nicht für die Nachrichtenweiterleitung angemedet")
        await interaction.delete_original_response()
