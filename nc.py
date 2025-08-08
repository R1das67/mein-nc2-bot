import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timezone
import os
import asyncio
from keep_alive import keep_alive

# ==== Konfiguration ====
TOKEN = os.getenv("DISCORD_TOKEN") or "DEIN_BOT_TOKEN_HIER"

TIMEOUT_WHITELIST = {
    662596869221908480,
    843180408152784936,
    1159469934989025290,
    830212609961754654,
    1322832586829205505,
}

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Cache für Timeouts
timeout_cache = {}

# ==== Slash-Command ====
@tree.command(name="removetimeout", description="Entfernt alle aktiven Timeouts (nur für Berechtigte).")
@app_commands.describe(target="Zielgruppe (nur 'everyone' erlaubt)")
async def removetimeout(interaction: discord.Interaction, target: str):
    if interaction.user.id not in TIMEOUT_WHITELIST:
        await interaction.response.send_message("❌ Du bist nicht berechtigt, diesen Befehl zu verwenden.", ephemeral=True)
        return

    if target.lower() != "everyone":
        await interaction.response.send_message("❌ Ungültiges Ziel. Nur 'everyone' ist erlaubt.", ephemeral=True)
        return

    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("❌ Dieser Befehl funktioniert nur in einem Server.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    members_to_untimeout = []

    # Verwende fetch_member statt get_member
    for user_id in timeout_cache.keys():
        try:
            member = await guild.fetch_member(user_id)
            members_to_untimeout.append(member)
        except discord.NotFound:
            pass  # Mitglied ist nicht mehr auf dem Server
        except discord.HTTPException as e:
            print(f"❌ Fehler beim Abrufen von Member {user_id}: {e}")

    async def untimeout(member):
        try:
            await member.edit(communication_disabled_until=None, reason=f"Enttimeoutet durch {interaction.user}")
            return 1
        except Exception as e:
            print(f"❌ Fehler bei {member}: {e}")
            return 0

    semaphore = asyncio.Semaphore(25)

    async def sem_untimeout(m):
        async with semaphore:
            return await untimeout(m)

    results = await asyncio.gather(*(sem_untimeout(m) for m in members_to_untimeout))
    count = sum(results)

    await interaction.followup.send(f"✅ {count} Nutzer wurden enttimeoutet.")

# ==== Timeout-Cache Updater Task ====
@tasks.loop(minutes=5)
async def update_timeout_cache():
    await bot.wait_until_ready()
    print("🔄 Aktualisiere Timeout-Cache...")
    for guild in bot.guilds:
        try:
            await guild.chunk()
            now = datetime.now(timezone.utc)
            timeout_cache.clear()
            for member in guild.members:
                if member.communication_disabled_until and member.communication_disabled_until > now:
                    timeout_cache[member.id] = member.communication_disabled_until
            print(f"✅ {len(timeout_cache)} aktive Timeouts im Cache.")
        except Exception as e:
            print(f"❌ Fehler beim Aktualisieren des Caches: {e}")

# ==== Bot Events ====
@bot.event
async def on_ready():
    print(f"✅ Bot ist online als {bot.user}")
    try:
        synced = await tree.sync()
        print(f"🔃 {len(synced)} Slash-Commands synchronisiert.")
    except Exception as e:
        print(f"❌ Fehler beim Slash-Sync: {e}")
    update_timeout_cache.start()

# ==== Bot starten ====
keep_alive()

async def main():
    async with bot:
        await bot.start(TOKEN)

asyncio.run(main())
