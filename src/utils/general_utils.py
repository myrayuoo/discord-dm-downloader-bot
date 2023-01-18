import os
import gzip
import shutil
import warnings
import functools
from discord import Embed
import discord
from discord.ext import commands
from webcolors import CSS3_NAMES_TO_HEX as CSS3NTH


async def dm_user(bot, id, *args, **kwargs):
    user = await bot.fetch_user(id)
    return await user.send(**kwargs)


def create_error_embed(**kwargs):
    return Embed(color=hex_color('grey'), **kwargs)


def create_success_embed(**kwargs):
    return Embed(color=hex_color('white'), **kwargs)


def hex_color(color):
    if color not in CSS3NTH:
        return int(CSS3NTH['white'][1:], 16)
    color = int(CSS3NTH[color][1:], 16)
    return color

def get_username(ctx: commands.Context):
    return f'{ctx.author.display_name}#{ctx.author.discriminator}'

def get_username_from_interaction(interaction: discord.Interaction):
    return f'{interaction.user.display_name}#{interaction.user.display_name}'

def limit_string(string: str):
    return (string[:1021] + '...') if len(string) > 1024 else string


def deprecated(func):
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning,
                      stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)
        return func(*args, **kwargs)
    return new_func


def compress_file(in_path: str, out_path: str, delete_old: bool = True):
    if not os.path.isfile(in_path):
        return False

    with open(in_path, 'rb') as in_file, \
            gzip.open(out_path, 'wb') as out_file:
        shutil.copyfileobj(in_file, out_file)

    if delete_old:
        os.remove(in_path)

    return True

def string_size(string: str):
    return len(string.encode('utf-8'))