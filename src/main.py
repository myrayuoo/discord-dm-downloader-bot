import re
import os
import discord
import traceback
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from utils.slash_commands_bot import SlashCommandsBot
from utils.general_utils import create_error_embed

bot = SlashCommandsBot(
    command_prefix=commands.when_mentioned_or('->'),
    intents=discord.Intents.all(),
)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')


@bot.tree.error
async def on_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    traceback.print_exc()

    error_desc = str(error)
    sep_index = error_desc.find(':')
    error_message = error_desc[sep_index:].strip().replace(':', '')
    words = [word.lower() for word in re.findall('[A-Z][^A-Z]*', error_message)] 
    
    if 'exception' in words[-1]:
        words.pop(-1)

    words[0].title()
    error_message = f'{error_desc[:sep_index]}: ```{" ".join(words)}```'

    embed = create_error_embed(description=error_message)
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed)
    else:
        await interaction.response.send_message(embed=embed)


def main():
    load_dotenv()

    bot.remove_command('help')
    bot.run(os.getenv('TOKEN'))


if __name__ == '__main__':
    main()
