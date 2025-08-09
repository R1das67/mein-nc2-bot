import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import time
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

# ==== Bot Setup ====
intents = discord.Intents.default()
intents.guilds = True
intents.members = True  # Wichtig für vollständige Member-Liste

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ==== Hilfsfunktion: Prüfen ob Timeout aktiv ====
def is_timed_out(member: discord.Member) -> bool:
    return member.communication_disabled_until is not None and member.communication_disabled_until > discord.utils.utcnow()

# ==== Slash-Command /removetimeout everyone ====
@tree.command(name="removetimeout", description="Entfernt alle aktiven Timeouts.")
@app_commands.describe(target="Zielgruppe (nur 'everyone' erlaubt)")
async def removetimeout(interaction: discord.Interaction, target: str):
    if interaction.user.id not in TIMEOUT_WHITELIST:
        await interaction.response.send_message(
            "❌ Du bist nicht berechtigt, diesen Befehl zu verwenden.",
            ephemeral=True
        )
        return

    if target.lower() != "everyone":
        await interaction.response.send_message(
            "❌ Ungültiges Ziel. Nur 'everyone' ist erlaubt.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    failed = []
    count = 0
    skipped = 0
    processed = 0

    members = [m async for m in guild.fetch_members(limit=None)]
    total_members = len(members)

    start_time = time.time()
    progress_msg = await interaction.followup.send(
        f"⏳ Starte Enttimeouten...\n0/{total_members} Mitglieder überprüft.",
        ephemeral=True
    )

    for member in members:
        try:
            if not is_timed_out(member):
                skipped += 1
            else:
                await member.edit(communication_disabled_until=None)
                count += 1
        except Exception as e:
            failed.append(str(member.id))
            print(f"Fehler beim Entfernen des Timeouts für {member.id}: {e}")

        processed += 1

        # Fortschritt alle 50 Mitglieder aktualisieren
        if processed % 50 == 0 or processed == total_members:
            elapsed = time.time() - start_time
            speed = processed / elapsed if elapsed > 0 else 0
            remaining = (total_members - processed) / speed if speed > 0 else 0
            await progress_msg.edit(content=(
                f"⏳ Enttimeouten läuft...\n"
                f"**{processed}/{total_members}** Mitglieder überprüft.\n"
                f"✅ {count} entfernt | 📋 {skipped} übersprungen | ⚠️ {len(failed)} Fehler\n"
                f"⏱ Geschätzte Restzeit: ~{remaining:.1f}s"
            ))

    # Ergebnis ausgeben
    msg = f"✅ {count} Nutzer wurden enttimeoutet."
    if skipped > 0:
        msg += f"\n📋 {skipped} Nutzer waren bereits nicht getimeoutet."
    if failed:
        msg += f"\n⚠️ Fehler bei folgenden User-IDs: {', '.join(failed)}"

    await progress_msg.edit(content=msg)

# ==== Event: Bot ist bereit ====
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

# ==== Bot starten ====
async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
