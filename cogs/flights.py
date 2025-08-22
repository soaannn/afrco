import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone

ROLE_ID_ALLOWED = 1380235072833060926
SOURCE_GUILD_ID = 1379545311982387261
TARGET_GUILD_ID = 1218246842719010926
ANNOUNCE_CHANNEL_ID = 1379838712808079522
LOCAL_IMAGE_PATH = "assets/flight.png"

class Flights(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.airports = {
            "AJA": "Ajaccio Napoléon Bonaparte Airport",
            "BER": "Berlin Brandenburg Airport",
            "CDG": "Paris Charles de Gaulle Airport",
            "ORY": "Paris Orly Airport",
            "KRK": "Kraków John Paul II International Airport"
        }
        self.allowed_airport_codes = set(self.airports.keys())
        self.flight_embed_message = None
        self.update_embed_task.start()

    def get_airport_name(self, code):
        return self.airports.get(code.upper(), "N/A")

    def get_airport_code_from_name(self, name):
        name = name.strip().lower()
        for code, full_name in self.airports.items():
            if name == code.lower() or name == full_name.lower():
                return code
        return "N/A"

    @app_commands.command(name="createflight", description="Schedule a new flight.")
    @app_commands.guilds(discord.Object(id=SOURCE_GUILD_ID))
    async def createflight(
        self,
        interaction: discord.Interaction,
        date: str,  # Format dd/mm/yy
        time: str,  # Format HH:MM 24h UTC
        flight_number: str,
        departure: str,
        arrival: str,
        aircraft: str
    ):
        # Vérification de rôle (manuel, car @checks.has_role ne fonctionne pas ici)
        if not any(role.id == ROLE_ID_ALLOWED for role in interaction.user.roles):
            await interaction.response.send_message("<:AF40:1386882112644321321> **You do not have permission to use this command**.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)

        try:
            dt = datetime.strptime(f"{date} {time}", "%d/%m/%y %H:%M").replace(tzinfo=timezone.utc)
            if dt <= datetime.now(timezone.utc):
                await interaction.followup.send("<:AF50:1386881978791362590> The date and time must be in the future.", ephemeral=True)
                return
            end_time = dt + timedelta(minutes=45)
        except Exception:
            await interaction.followup.send("<:AF50:1386881978791362590> Invalid date/time format. Use: dd/mm/yy HH:MM (24h format).", ephemeral=True)
            return

        departure_full = self.get_airport_name(departure)
        arrival_full = self.get_airport_name(arrival)

        event_name = flight_number
        event_description = (
            f"The flight **{flight_number}** has been successfully **scheduled** to operate the route "
            f"from **{departure.upper()}** to **{arrival.upper()}**. We recommend arriving **15 minutes before boarding**. "
            f"Air France wishes you a **pleasant flight** aboard our **{aircraft}**."
        )

        try:
            with open(LOCAL_IMAGE_PATH, "rb") as f:
                image_bytes = f.read()
        except Exception:
            await interaction.followup.send("<:AF50:1386881978791362590> Failed to load the event banner image.", ephemeral=True)
            print(f"[ERROR] Loading image.")
            return

        target_guild = self.bot.get_guild(TARGET_GUILD_ID)
        if not target_guild:
            await interaction.followup.send("<:AF50:1386881978791362590> Failed to access the target guild.", ephemeral=True)
            return

        try:
            await target_guild.create_scheduled_event(
                name=event_name,
                start_time=dt,
                end_time=end_time,
                description=event_description,
                entity_type=discord.EntityType.external,
                location=departure_full,
                privacy_level=discord.PrivacyLevel.guild_only,
                image=image_bytes
            )
        except Exception:
            await interaction.followup.send("<:AF50:1386881978791362590> Failed to create the scheduled event.", ephemeral=True)
            return

        embed = discord.Embed(
            title="<:AF9:1386882613347745987> Flight Scheduled.",
            color=0x1d2c79,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="<:AF_BLUE:1387172285898690640> Flight Number", value=flight_number, inline=True)
        embed.add_field(name="<:AF2:1387028053850460222> Time (UTC)", value=f"{date} {time}", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.add_field(name="<:AF44:1386882057019457556> Departure", value=f"{departure.upper()} - {departure_full}", inline=True)
        embed.add_field(name="<:AF45:1386882043731902565> Arrival", value=f"{arrival.upper()} - {arrival_full}", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.add_field(name="<:AF52:1386881951721586788> Aircraft", value=aircraft, inline=True)
        embed.add_field(name="<:AF5:1386882667177443328> Dispatcher", value=interaction.user.mention, inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        await interaction.followup.send(embed=embed, ephemeral=False)


    @tasks.loop(seconds=60)
    async def update_embed_task(self):
        try:
            guild = self.bot.get_guild(TARGET_GUILD_ID)
            if not guild:
                return
            channel = guild.get_channel(ANNOUNCE_CHANNEL_ID)
            if not channel:
                return

            events = await guild.fetch_scheduled_events()
            now = datetime.now(timezone.utc)
            upcoming = []

            for event in events:
                if not event.start_time:
                    continue
                if timedelta(0) <= (event.start_time - now) <= timedelta(days=5):
                    dep = arr = "N/A"
                    fname = event.name
                    desc = event.description or ""
                    if "from **" in desc and "to **" in desc:
                        try:
                            parts = desc.split("from **")[1].split("** to **")
                            dep = parts[0].strip()
                            arr = parts[1].split("**")[0].strip()
                        except:
                            pass
                    dep_code = self.get_airport_code_from_name(dep)
                    arr_code = self.get_airport_code_from_name(arr)
                    if dep_code in self.allowed_airport_codes and arr_code in self.allowed_airport_codes:
                        upcoming.append((dep_code, arr_code, event.start_time, event.id, fname))

            embed = discord.Embed(
                title="<:AF_FRFLAG:1387070700967165982> **Departure Board**",
                color=0x1d2c79
            )

            embed.set_footer(
                text="Once a flight is hosted, please click on the event card for itinerary information. We wish you a pleasant journey!"
            )

            if upcoming:
                content_lines = []
                for dep, arr, stime, eid, fname in sorted(upcoming, key=lambda x: x[2]):
                    ts = int(stime.timestamp())
                    link = f"https://discord.com/events/{TARGET_GUILD_ID}/{eid}"
                    line = f"**{dep}** to **{arr}** | [**{fname}**]({link}), <t:{ts}:F>."
                    content_lines.append(line)
                embed.description = "\n".join(content_lines)
            else:
                embed.description = "> There are currently no flights operated by our main airline, <:AFTAIL:1379835361517113415> **Air France**, or any of our subsidiaries."

            if not self.flight_embed_message:
                async for msg in channel.history(limit=10):
                    if msg.author == guild.me and msg.embeds:
                        await msg.delete()
                self.flight_embed_message = await channel.send(embed=embed)
            else:
                await self.flight_embed_message.edit(embed=embed)

            print("[INFO] Flight embed updated.")

        except Exception as e:
            print(f"[ERROR] Updating embed: {e}")

    @update_embed_task.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Flights(bot))
