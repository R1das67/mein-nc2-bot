import discord
from discord.ext import commands
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

keep_alive()  # Webserver starten (z.B. für UptimeRobot)

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

    await guild.chunk()  # Alle Mitglieder in den Cache laden

    now = datetime.now(timezone.utc)
    members_to_untimeout = [
        member for member in guild.members
        if member.communication_disabled_until and member.communication_disabled_until > now
    ]

    async def untimeout(member):
        try:
            await member.edit(communication_disabled_until=None, reason=f"Enttimeoutet durch {interaction.user}")
            return 1
        except Exception as e:
            print(f"❌ Fehler bei {member}: {e}")
            return 0

    semaphore = asyncio.Semaphore(25)  # max 25 parallel

    async def sem_untimeout(m):
        async with semaphore:
            return await untimeout(m)

    results = await asyncio.gather(*(sem_untimeout(m) for m in members_to_untimeout))
    count = sum(results)

    await interaction.followup.send(f"✅ {count} Nutzer wurden enttimeoutet.")

@bot.event
async def on_ready():
    print(f"✅ Bot ist online als {bot.user}")
    try:
        synced = await tree.sync()
        print(f"🔃 {len(synced)} Slash-Commands synchronisiert.")
    except Exception as e:
        print(f"❌ Fehler beim Slash-Sync: {e}")

async def main():
    async with bot:
        await bot.start(TOKEN)

asyncio.run(main())
