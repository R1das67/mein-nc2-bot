import discord
from discord.ext import commands
from discord import app_commands, AuditLogAction
from datetime import datetime, timezone
import os
import asyncio
from keep_alive import keep_alive

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
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ==== Slash-Command ====
@tree.command(name="removetimeout", description="Entfernt alle aktiven Timeouts basierend auf dem Audit-Log.")
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
    processed_ids = set()
    count = 0

    try:
        async for entry in guild.audit_logs(limit=150, action=AuditLogAction.member_update):
            if not entry.after or not hasattr(entry.after, "communication_disabled_until"):
                continue

            timeout_until = entry.after.communication_disabled_until
            if timeout_until and timeout_until > now:
                target_user = entry.target
                if target_user.id in processed_ids:
                    continue
                processed_ids.add(target_user.id)

                try:
                    member = await guild.fetch_member(target_user.id)
                    await member.edit(communication_disabled_until=None, reason=f"Enttimeoutet durch {interaction.user}")
                    count += 1
                except Exception as e:
                    print(f"❌ Fehler bei {target_user}: {e}")

        await interaction.followup.send(f"✅ {count} Nutzer wurden enttimeoutet (basierend auf Audit-Log).")

    except discord.Forbidden:
        await interaction.followup.send("❌ Ich habe keine Berechtigung, das Audit-Log zu lesen.")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        await interaction.followup.send("❌ Ein Fehler ist aufgetreten.")

# ==== Events ====
@bot.event
async def on_ready():
    print(f"✅ Bot ist online als {bot.user}")
    try:
        synced = await tree.sync()
        print(f"🔃 {len(synced)} Slash-Commands synchronisiert.")
    except Exception as e:
        print(f"❌ Fehler beim Slash-Sync: {e}")

# ==== Bot starten ====
keep_alive()

async def main():
    async with bot:
        await bot.start(TOKEN)

asyncio.run(main())
