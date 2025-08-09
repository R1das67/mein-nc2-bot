import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import time
from keep_alive import keep_alive  # Falls du das brauchst

# ==== Konfiguration ====
TOKEN = os.getenv("DISCORD_TOKEN") or "DEIN_BOT_TOKEN_HIER"

# Nutzer-IDs, die den Command ausführen dürfen
TIMEOUT_WHITELIST = {
    662596869221908480,
    843180408152784936,
    1159469934989025290,
    830212609961754654,
    1322832586829205505,
}

# ==== Intents ====
intents = discord.Intents.default()
intents.guilds = True
intents.members = True  # Wichtig, um alle Mitglieder zu bekommen

# ==== Bot Setup ====
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ==== /removetimeout everyone Command ====
@tree.command(name="removetimeout", description="Entfernt alle aktiven Timeouts aller Mitglieder.")
@app_commands.describe(target="Zielgruppe (nur 'everyone' erlaubt)")
async def removetimeout(interaction: discord.Interaction, target: str):
    # Rechteprüfung
    if interaction.user.id not in TIMEOUT_WHITELIST:
        await interaction.response.send_message("❌ Du hast keine Berechtigung für diesen Befehl.", ephemeral=True)
        return

    # Nur "everyone" erlaubt
    if target.lower() != "everyone":
        await interaction.response.send_message("❌ Ungültiges Ziel. Nur 'everyone' ist erlaubt.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    if guild is None:
        await interaction.followup.send("❌ Fehler: Kein gültiger Server kontext.", ephemeral=True)
        return

    failed_ids = []
    removed_count = 0
    skipped_count = 0

    # Mitglieder asynchron abrufen
    members = [m async for m in guild.fetch_members(limit=None)]
    total_members = len(members)

    start_time = time.time()
    progress_message = await interaction.followup.send(
        f"⏳ Starte Timeout-Entfernung bei {total_members} Mitgliedern...", ephemeral=True
    )

    processed = 0
    for member in members:
        try:
            # fresh fetch, um aktuellen Timeout-Status zu sichern
            fresh_member = await guild.fetch_member(member.id)
            if fresh_member.timed_out:
                await fresh_member.edit(timed_out_until=None)
                removed_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            failed_ids.append(str(member.id))
            print(f"Fehler beim Entfernen des Timeouts für {member.id}: {e}")

        processed += 1

        # Fortschritt alle 50 Mitglieder aktualisieren
        if processed % 50 == 0 or processed == total_members:
            elapsed = time.time() - start_time
            speed = processed / elapsed if elapsed > 0 else 0
            remaining = (total_members - processed) / speed if speed > 0 else 0
            await progress_message.edit(content=(
                f"⏳ Timeout-Entfernung läuft...\n"
                f"**{processed}/{total_members}** Mitglieder überprüft.\n"
                f"✅ {removed_count} enttimeoutet | 📋 {skipped_count} übersprungen | ⚠️ {len(failed_ids)} Fehler\n"
                f"⏱ Geschätzte Restzeit: ~{remaining:.1f}s"
            ))

    # Abschließende Zusammenfassung
    summary = (
        f"✅ Timeout-Entfernung abgeschlossen.\n"
        f"✅ Insgesamt enttimeoutet: {removed_count}\n"
        f"📋 Bereits nicht getimeoutet: {skipped_count}"
    )
    if failed_ids:
        summary += f"\n⚠️ Fehler bei User-IDs: {', '.join(failed_ids)}"

    await progress_message.edit(content=summary)


# ==== on_ready Event ====
@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")
    try:
        synced = await tree.sync()
        print(f"🔃 {len(synced)} Slash-Commands synchronisiert.")
    except Exception as e:
        print(f"❌ Fehler beim Synchronisieren der Slash-Commands: {e}")


# ==== keep_alive starten (optional) ====
keep_alive()

# ==== Bot starten ====
async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
