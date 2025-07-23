import discord as dc
from discord import app_commands

class WhisperCog(dc.ext.commands.Cog):
    '''
    Cog for sending messages anonymously
    '''
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="whisper", description="Sag etwas, aber bleib dabei anonym")
    async def whisper(self, interaction: dc.Interaction, message: str):
        '''so simple it doesn't need a docstring'''
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.send(message)
        await interaction.delete_original_response()
