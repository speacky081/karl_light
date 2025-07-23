import os.path
import discord as dc
from discord import app_commands

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

    @app_commands.command(
        name="whisper", description="Sag etwas, aber bleib dabei anonym")
    async def whisper(self, interaction: dc.Interaction, message: str):
        '''so simple it doesn't need a docstring'''
        await interaction.response.defer(ephemeral=True)
        channel = self.bot.get_channel(1397636825971032095)
        if channel is None:
            channel = await self.bot.fetch_channel(1397636825971032095)
        await channel.send(" \n" + "**ANONYM **" + message)
        with open("whisper_clients.txt", "r", encoding="utf-8") as clients:
            self.clients = [line.strip() for line in clients]
        for client in self.clients:
            channel = await self.bot.fetch_user(int(client))
            await channel.send(" \n" + "**ANONYM **" + message)
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
