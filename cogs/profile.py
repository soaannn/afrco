import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timezone

PRIMARY_GUILD_ID = 1380598262758768834
SECONDARY_GUILD_ID = 1379545311982387261
PRIMARY_ROLE_ID = 1380598262779744277
SECONDARY_ROLE_ID = 1379548869217488986

PRIMARY_DB = "databases/database.json"
SECONDARY_DB = "databases/personneldatabase.json"

CHECKMARK_EMOJI = "<:Frame748:1386880189635625090>"
CROSS_EMOJI = "<:Frame739:1386880162762723398>"

def iso_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def format_timestamp(iso_str: str | None) -> str:
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        unix_ts = int(dt.timestamp())
        return f"<t:{unix_ts}:F>"
    except Exception:
        return ""

def load_data(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_membership(self, user: discord.User):
        primary_guild = self.bot.get_guild(PRIMARY_GUILD_ID)
        secondary_guild = self.bot.get_guild(SECONDARY_GUILD_ID)

        in_primary = primary_guild.get_member(user.id) if primary_guild else None
        in_secondary = secondary_guild.get_member(user.id) if secondary_guild else None

        return in_primary or in_secondary

    def has_required_role(self, member: discord.Member, role_id: int) -> bool:
        return any(role.id == role_id for role in member.roles)

    @app_commands.command(name="profile", description="Display a profile.")
    async def profile(self, interaction: discord.Interaction, user: discord.User | None = None):
        if not await self.check_membership(interaction.user):
            await interaction.response.send_message(
                "<:AF40:1386882112644321321> **You do not have permission to use this command**.",
                ephemeral=True
            )
            return

        await interaction.response.defer()
        target = user or interaction.user
        user_id = str(target.id)

        if interaction.guild_id == PRIMARY_GUILD_ID:
            data = load_data(PRIMARY_DB)
            profile = data.get(user_id)
            if not profile:
                await interaction.followup.send("<:Frame773:1386880273865511053> No data was found for your profile.")
                return

            roblox = profile.get("roblox_username", "N/A")
            department = profile.get("department", "N/A")
            notes = profile.get("notes", "N/A")

            embed = discord.Embed(color=discord.Color(0x0c1649))
            embed.add_field(name="Discord Username", value=target.name, inline=True)
            embed.add_field(name="Roblox Username", value=roblox, inline=True)
            embed.add_field(name="Department", value=department, inline=True)
            embed.add_field(name="Notes", value=notes, inline=True)

            # Phase 1
            p1_done = profile.get("phase1_done", False)
            p1_ts = format_timestamp(profile.get("phase1_timestamp"))
            p1_val = f"{CHECKMARK_EMOJI} {p1_ts}" if p1_done else CROSS_EMOJI
            embed.add_field(name="Phase 1", value=p1_val, inline=True)

            # Phase 2
            p2_done = profile.get("phase2_done", False)
            p2_ts = format_timestamp(profile.get("phase2_timestamp"))
            p2_val = f"{CHECKMARK_EMOJI} {p2_ts}" if p2_done else CROSS_EMOJI
            embed.add_field(name="Phase 2", value=p2_val, inline=True)

            # Final Exam (Cabin Crew & Flight Deck)
            if department in ["Cabin Crew", "Flight Deck"]:
                final_done = profile.get("final_done", False)
                final_ts = format_timestamp(profile.get("final_timestamp"))
                embed.add_field(name="Final Examination", value=f"{CHECKMARK_EMOJI} {final_ts}" if final_done else CROSS_EMOJI, inline=True)

            await interaction.followup.send(embed=embed)

        elif interaction.guild_id == SECONDARY_GUILD_ID:
            data = load_data(SECONDARY_DB)
            profile = data.get(user_id)
            if not profile:
                await interaction.followup.send("No data was found for your profile.")
                return

            roblox = profile.get("roblox_username", "N/A")
            flights = profile.get("flights_attended", 0)
            strikes = profile.get("strikes", 0)
            notes = profile.get("notes", "N/A")

            embed = discord.Embed(color=discord.Color(0x0c1649))
            embed.add_field(name="Discord Username", value=target.name, inline=True)
            embed.add_field(name="Roblox Username", value=roblox, inline=True)
            embed.add_field(name="Flight Points", value=str(flights), inline=True)
            embed.add_field(name="Strikes", value=str(strikes), inline=True)
            embed.add_field(name="Notes", value=notes, inline=True)

            await interaction.followup.send(embed=embed)

    @app_commands.command(name="asetprofile", description="Set or update an academy profile.")
    async def asetprofile(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        roblox_username: str,
        department: str,
        notes: str | None = None,
        phase1: str = "no",
        phase2: str = "no",
        final_exam: str = "no"
    ):
        if not await self.check_membership(interaction.user):
            await interaction.response.send_message(
                "<:AF40:1386882112644321321> **You do not have permission to use this command**.",
                ephemeral=True
            )
            return

        if interaction.guild_id != PRIMARY_GUILD_ID:
            await interaction.response.send_message(
                "<:AF40:1386882112644321321> **You do not have permission to use this command**.",
                ephemeral=True
            )
            return

        member = interaction.user
        if not isinstance(member, discord.Member) or not self.has_required_role(member, PRIMARY_ROLE_ID):
            await interaction.response.send_message(
                "<:AF40:1386882112644321321> **You do not have permission to use this command**.",
                ephemeral=True
            )
            return

        profile_data = {
            "roblox_username": roblox_username,
            "department": department,
            "notes": notes or "N/A",
            "phase1_done": phase1.lower() == "yes",
            "phase1_timestamp": iso_now() if phase1.lower() == "yes" else None,
            "phase2_done": phase2.lower() == "yes",
            "phase2_timestamp": iso_now() if phase2.lower() == "yes" else None
        }

        if department in ["Cabin Crew", "Flight Deck"]:
            profile_data["final_done"] = final_exam.lower() == "yes"
            profile_data["final_timestamp"] = iso_now() if final_exam.lower() == "yes" else None

        data = load_data(PRIMARY_DB)
        data[str(user.id)] = profile_data
        save_data(PRIMARY_DB, data)

        await interaction.response.send_message(f"✅ Academy profile updated for **{user.display_name}**.")

    @app_commands.command(name="psetprofile", description="Set or update a personnel profile.")
    async def psetprofile(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        roblox_username: str,
        flights_attended: int,
        strikes: int,
        notes: str | None = None
    ):
        if not await self.check_membership(interaction.user):
            await interaction.response.send_message(
                "<:AF40:1386882112644321321> **You do not have permission to use this command**.",
                ephemeral=True
            )
            return

        if interaction.guild_id != SECONDARY_GUILD_ID:
            await interaction.response.send_message(
                "<:AF40:1386882112644321321> **You do not have permission to use this command**.",
                ephemeral=True
            )
            return

        member = interaction.user
        if not isinstance(member, discord.Member) or not self.has_required_role(member, SECONDARY_ROLE_ID):
            await interaction.response.send_message(
                "<:AF40:1386882112644321321> **You do not have permission to use this command**.",
                ephemeral=True
            )
            return

        data = load_data(SECONDARY_DB)
        data[str(user.id)] = {
            "roblox_username": roblox_username,
            "flights_attended": flights_attended,
            "strikes": strikes,
            "notes": notes or "N/A",
            "updated_at": iso_now()
        }
        save_data(SECONDARY_DB, data)
        await interaction.response.send_message(f"✅ Personnel profile updated for **{user.display_name}**.")

async def setup(bot):
    await bot.add_cog(Profile(bot))
