import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import os
import asyncio
from keep_alive import keep_alive

keep_alive()

# ==== Konfiguration ====
TOKEN = os.getenv("DISCORD_TOKEN") or "DEIN_BOT_TOKEN_HIER"

# ✅ Whitelist: Nur diese User-IDs dürfen /removetimeout verwenden
TIMEOUT_WHITELIST = {
    662596869221908480,
    843180408152784936,
    1159469934989025290,
    830212609961754654,
    1322832586829205505,
}

# ==== Bot Setup ====
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ==== Slash-Command ====
@tree.command(name="removetimeout", description="Entfernt aktive Timeouts basierend auf Audit-Log (nur für Berechtigte).")
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
    seen_user_ids = set()

    # Gehe die letzten 150 Audit-Log-Einträge durch
    async for entry in guild.audit_logs(limit=150, action=discord.AuditLogAction.member_update):
        member = entry.target

        # Vermeide doppelte Verarbeitung
        if not isinstance(member, discord.Member):
            continue
        if member.id in seen_user_ids:
            continue
        seen_user_ids.add(member.id)

        # Prüfen, ob Timeout gesetzt wurde und noch aktiv ist
        before = entry.before
        after = entry.after

        if (
            hasattr(before, "communication_disabled_until")
            and hasattr(after, "communication_disabled_until")
            and (before.communication_disabled_until != after.communication_disabled_until)
            and after.communication_disabled_until
            and after.communication_disabled_until > now
        ):
            try:
                await member.edit(communication_disabled_until=None, reason=f"Enttimeoutet durch {interaction.user}")
                count += 1
            except Exception as e:
                print(f"❌ Fehler bei {member}: {e}")

    await interaction.followup.send(f"✅ {count} Nutzer wurden per Audit-Log enttimeoutet.")

# ==== Bot Events ====
@bot.event
async def on_ready():
    print(f"✅ Bot ist online als {bot.user}")
    try:
        synced = await tree.sync()
        print(f"🔃 {len(synced)} Slash-Commands synchronisiert.")
    except Exception as e:
        print(f"❌ Fehler beim Slash-Sync: {e}")

# ==== Bot starten ====
async def main():
    async with bot:
        await bot.start(TOKEN)

asyncio.run(main())
