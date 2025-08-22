import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True  # <--- Important

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game("supervising you.")
    )
    print(f"✅ Logged in as {bot.user.name} ({bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"[ERROR] Slash command sync failed: {e}")

async def load_extensions():
    for root, dirs, files in os.walk("cogs"):
        for file in files:
            if file.endswith(".py"):
                # Transforme le chemin en nom de module Python (ex: cogs.subfolder.module)
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, ".").replace(os.sep, ".")
                module_name = relative_path[:-3]  # Supprime ".py"
                try:
                    await bot.load_extension(module_name)
                    print(f"[DEBUG] Loaded {module_name}")
                except Exception as e:
                    print(f"[ERROR] Failed to load {module_name}: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
