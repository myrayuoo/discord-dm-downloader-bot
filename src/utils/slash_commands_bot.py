import os
from discord.ext import commands


class SlashCommandsBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.synced = False
        self.cogs_dir = kwargs.get('cogs_dir', './src')

    async def setup_hook(self) -> None:
        for dirpath, dirnames, filenames in os.walk(self.cogs_dir):
            for fn in filenames:
                if fn.endswith('_cog.py'):
                    cog = fn[:-3]
                    await self.load_extension(cog)
            break
        if not self.synced:
            await self.tree.sync()
            self.synced = True
