import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import os
import asyncio
from keep_alive import keep_alive  # Falls du keep_alive nutzt

# ==== Konfiguration ====
TOKEN = os.getenv("DISCORD_TOKEN") or "DEIN_BOT_TOKEN_HIER"

TIMEOUT_WHITELIST = {
    662596869221908480,
    843180408152784936,
    1159469934989025290,
    830212609961754654,
    1322832586829205505,
}

# ==== Bot Setup ====
intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ==== Slash-Command /removetimeout everyone ====
@tree.command(name="removetimeout", description="Entfernt alle aktiven Timeouts.")
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

    now = datetime.now(timezone.utc)
    count = 0
    failed = []

    async for member in guild.fetch_members(limit=None):
        try:
            if member.communication_disabled_until and member.communication_disabled_until > now:
                await member.edit(communication_disabled_until=None, reason=f"Timeout entfernt durch {interaction.user}")
                count += 1
        except Exception as e:
            failed.append(str(member.id))
            print(f"❌ Fehler bei User {member}: {e}")

    msg = f"✅ {count} Nutzer wurden enttimeoutet."
    if failed:
        msg += f"\n⚠️ Fehler bei folgenden User-IDs: {', '.join(failed)}"

    await interaction.followup.send(msg)

# ==== Event: Bot ist bereit ====
@bot.event
async def on_ready():
    print(f"✅ Bot ist online als {bot.user}")
    try:
        synced = await tree.sync()
        print(f"🔃 {len(synced)} Slash-Commands synchronisiert.")
    except Exception as e:
        print(f"❌ Fehler beim Slash-Sync: {e}")

# ==== keep_alive starten (falls vorhanden) ====
keep_alive()

# ==== Bot starten ====
async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
