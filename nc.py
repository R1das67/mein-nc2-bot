import discord
from discord.ext import commands
from discord import app_commands
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

    # Erst Discord sagen, dass wir länger brauchen werden
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    failed = []
    count = 0
    skipped = 0

    async for member in guild.fetch_members():
        try:
            if not member.timed_out:
                skipped += 1
                continue

            await member.edit(timed_out_until=None)
            count += 1
        except Exception as e:
            failed.append(str(member.id))
            print(f"Failed to remove timeout for {member.id}: {e}")

    msg = f"✅ {count} Nutzer wurden enttimeoutet."
    if skipped > 0:
        msg += f"\n📋 {skipped} Nutzer waren bereits nicht getimeoutet."
    if failed:
        msg += f"\n⚠️ Fehler bei folgenden User-IDs: {', '.join(failed)}"

    # Nach Abschluss die finale Antwort senden
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

# ==== keep_alive starten ====
keep_alive()

# ==== Bot starten ====
async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
