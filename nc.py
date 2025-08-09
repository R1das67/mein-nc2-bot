import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from keep_alive import keep_alive
import time

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

    members = [m async for m in guild.fetch_members()]
    total_members = len(members)

    start_time = time.time()
    progress_msg = await interaction.followup.send(
        f"⏳ Starte Enttimeouten...\n0/{total_members} Mitglieder überprüft.",
        ephemeral=True
    )

    # Erste Runde Timeout entfernen
    processed = 0
    for member in members:
        try:
            if not member.timed_out:
                skipped += 1
            else:
                await member.edit(timed_out_until=None)
                count += 1
        except Exception as e:
            failed.append(str(member.id))
            print(f"Failed to remove timeout for {member.id}: {e}")

        processed += 1

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

    # Kurze Pause, damit Status sich aktualisiert
    await asyncio.sleep(3)
    members = [m async for m in guild.fetch_members()]

    # Zweite Runde Timeout entfernen (letzter Check)
    count2 = 0
    skipped2 = 0
    failed2 = []
    processed = 0
    for member in members:
        try:
            if not member.timed_out:
                skipped2 += 1
            else:
                await member.edit(timed_out_until=None)
                count2 += 1
        except Exception as e:
            failed2.append(str(member.id))
            print(f"Failed 2nd round to remove timeout for {member.id}: {e}")

        processed += 1

        if processed % 50 == 0 or processed == total_members:
            await progress_msg.edit(content=(
                f"⏳ 2. Durchlauf läuft...\n"
                f"**{processed}/{total_members}** Mitglieder überprüft.\n"
                f"✅ {count + count2} entfernt | 📋 {skipped + skipped2} übersprungen | ⚠️ {len(failed) + len(failed2)} Fehler\n"
            ))

    # Endergebnis
    total_removed = count + count2
    total_skipped = skipped + skipped2
    total_failed = failed + failed2

    msg = f"✅ Insgesamt {total_removed} Nutzer wurden enttimeoutet."
    if total_skipped > 0:
        msg += f"\n📋 {total_skipped} Nutzer waren bereits nicht getimeoutet."
    if total_failed:
        msg += f"\n⚠️ Fehler bei folgenden User-IDs: {', '.join(total_failed)}"

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
