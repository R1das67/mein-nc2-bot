import discord
from discord.ext import commands, tasks
from discord import app_commands, AuditLogAction
from datetime import datetime, timezone
import os
import asyncio
from keep_alive import keep_alive  # Import der keep_alive Funktion

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

timeout_cache = set()

async def load_timeouts(guild: discord.Guild):
    global timeout_cache
    timeout_cache.clear()

    now = datetime.now(timezone.utc)
    async for entry in guild.audit_logs(limit=200, action=AuditLogAction.member_update):
        after = entry.after
        if not after:
            continue
        timeout_until = getattr(after, "communication_disabled_until", None)
        if timeout_until and timeout_until > now:
            timeout_cache.add(entry.target.id)
    print(f"🔄 Timeout-Cache geladen: {len(timeout_cache)} User")

@tree.command(name="removetimeout", description="Entfernt alle aktiven Timeouts basierend auf dem Cache und Audit-Log.")
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

    await load_timeouts(guild)

    if not timeout_cache:
        await interaction.followup.send("ℹ️ Es sind keine aktiven Timeouts vorhanden.")
        return

    count = 0
    failed = []
    now = datetime.now(timezone.utc)

    to_process = timeout_cache.copy()

    for user_id in to_process:
        try:
            member = await guild.fetch_member(user_id)
            if member.communication_disabled_until and member.communication_disabled_until > now:
                await member.edit(communication_disabled_until=None, reason=f"Enttimeoutet durch {interaction.user} ({interaction.user.id})")
                count += 1
            timeout_cache.discard(user_id)
        except Exception as e:
            failed.append(str(user_id))
            print(f"❌ Fehler bei UserID {user_id}: {e}")

    msg = f"✅ {count} Nutzer wurden enttimeoutet."
    if failed:
        msg += f"\n⚠️ Fehler bei folgenden User-IDs: {', '.join(failed)}"

    await interaction.followup.send(msg)

@bot.event
async def on_ready():
    print(f"✅ Bot ist online als {bot.user}")
    try:
        synced = await tree.sync()
        print(f"🔃 {len(synced)} Slash-Commands synchronisiert.")
    except Exception as e:
        print(f"❌ Fehler beim Slash-Sync: {e}")

# ==== keep_alive starten ====
keep_alive()

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
