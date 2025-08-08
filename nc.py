import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import os
import asyncio
from keep_alive import keep_alive  # <- hier

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

keep_alive()  # <- und hier

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
    seen_ids = set()

    async for entry in guild.audit_logs(limit=150, action=discord.AuditLogAction.member_update):
        member = entry.target

        if not isinstance(member, discord.Member):
            continue
        if member.id in seen_ids:
            continue
        seen_ids.add(member.id)

        if member.communication_disabled_until and member.communication_disabled_until > now:
            try:
                await member.edit(communication_disabled_until=None, reason=f"Enttimeoutet durch {interaction.user}")
                count += 1
            except Exception as e:
                print(f"❌ Fehler bei {member}: {e}")

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
