import os
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv
import bcrypt

# =========================================================
# SETUP
# =========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
PASSWORD_HASH = os.getenv("PASSWORD_HASH").encode()

CONFIG_FILE = "channelcat_config.json"

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

authenticated_users = set()


# =========================================================
# CONFIG
# =========================================================

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {
            "locked_channels": {}
        }

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {
            "locked_channels": {}
        }


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4)


config = load_config()


# =========================================================
# SECURITY
# =========================================================

def is_owner(interaction: discord.Interaction):
    return interaction.user.id == OWNER_ID


async def security_check(interaction: discord.Interaction):

    if not is_owner(interaction):
        await interaction.response.send_message(
            "❌ You are not authorized to use ChannelCat.",
            ephemeral=True
        )
        return False

    if interaction.user.id not in authenticated_users:
        await interaction.response.send_message(
            "🔒 Please authenticate first using `/authenticate`.",
            ephemeral=True
        )
        return False

    return True


# =========================================================
# BOT READY
# =========================================================

@bot.event
async def on_ready():

    print(f"🐱 ChannelCat is online as {bot.user}")
    print(f"Connected to {len(bot.guilds)} server(s)")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Command sync error: {e}")


# =========================================================
# AUTHENTICATE
# =========================================================

@bot.tree.command(
    name="authenticate",
    description="Authenticate yourself to use ChannelCat."
)
async def authenticate(
    interaction: discord.Interaction,
    password: str
):

    if not is_owner(interaction):

        await interaction.response.send_message(
            "❌ You are not authorized to use ChannelCat.",
            ephemeral=True
        )

        return

    if bcrypt.checkpw(
        password.encode(),
        PASSWORD_HASH
    ):

        authenticated_users.add(interaction.user.id)

        await interaction.response.send_message(
            "✅ Authentication successful! ChannelCat management commands are unlocked.",
            ephemeral=True
        )

    else:

        await interaction.response.send_message(
            "❌ Incorrect management password.",
            ephemeral=True
        )


# =========================================================
# LOGOUT
# =========================================================

@bot.tree.command(
    name="logout",
    description="Log out of ChannelCat."
)
async def logout(
    interaction: discord.Interaction
):

    if not is_owner(interaction):

        await interaction.response.send_message(
            "❌ You are not authorized to use ChannelCat.",
            ephemeral=True
        )

        return

    authenticated_users.discard(
        interaction.user.id
    )

    await interaction.response.send_message(
        "🔒 Logged out successfully.",
        ephemeral=True
    )


# =========================================================
# CREATE CATEGORY
# =========================================================

@bot.tree.command(
    name="createcategory",
    description="Create a new channel category."
)
async def createcategory(
    interaction: discord.Interaction,
    name: str
):

    if not await security_check(interaction):
        return

    existing = discord.utils.get(
        interaction.guild.categories,
        name=name
    )

    if existing:

        await interaction.response.send_message(
            f"⚠️ Category **{name}** already exists.",
            ephemeral=True
        )

        return

    try:

        category = await interaction.guild.create_category(
            name,
            reason=f"ChannelCat category creation by {interaction.user}"
        )

        await interaction.response.send_message(
            f"✅ Created category {category.name}.",
            ephemeral=True
        )

    except Exception as e:

        await interaction.response.send_message(
            f"❌ Failed to create category:\n`{e}`",
            ephemeral=True
        )


# =========================================================
# CREATE TEXT CHANNEL
# =========================================================

@bot.tree.command(
    name="createchannel",
    description="Create a text channel."
)
async def createchannel(
    interaction: discord.Interaction,
    name: str,
    category: discord.CategoryChannel = None
):

    if not await security_check(interaction):
        return

    existing = discord.utils.get(
        interaction.guild.text_channels,
        name=name
    )

    if existing:

        await interaction.response.send_message(
            f"⚠️ Text channel **#{name}** already exists.",
            ephemeral=True
        )

        return

    try:

        channel = await interaction.guild.create_text_channel(
            name,
            category=category,
            reason=f"ChannelCat text channel creation by {interaction.user}"
        )

        await interaction.response.send_message(
            f"✅ Created {channel.mention}.",
            ephemeral=True
        )

    except Exception as e:

        await interaction.response.send_message(
            f"❌ Failed to create channel:\n`{e}`",
            ephemeral=True
        )


# =========================================================
# CREATE VOICE CHANNEL
# =========================================================

@bot.tree.command(
    name="createvoice",
    description="Create a voice channel."
)
async def createvoice(
    interaction: discord.Interaction,
    name: str,
    category: discord.CategoryChannel = None
):

    if not await security_check(interaction):
        return

    existing = discord.utils.get(
        interaction.guild.voice_channels,
        name=name
    )

    if existing:

        await interaction.response.send_message(
            f"⚠️ Voice channel **{name}** already exists.",
            ephemeral=True
        )

        return

    try:

        channel = await interaction.guild.create_voice_channel(
            name,
            category=category,
            reason=f"ChannelCat voice channel creation by {interaction.user}"
        )

        await interaction.response.send_message(
            f"✅ Created voice channel **{channel.name}**.",
            ephemeral=True
        )

    except Exception as e:

        await interaction.response.send_message(
            f"❌ Failed to create voice channel:\n`{e}`",
            ephemeral=True
        )


# =========================================================
# CREATE CHANNELS FROM TXT
# =========================================================

@bot.tree.command(
    name="createchannels",
    description="Create channels and categories from a TXT file."
)
async def createchannels(
    interaction: discord.Interaction,
    file: discord.Attachment
):

    if not await security_check(interaction):
        return

    if not file.filename.lower().endswith(".txt"):

        await interaction.response.send_message(
            "❌ Please upload a `.txt` file.",
            ephemeral=True
        )

        return

    await interaction.response.defer(
        ephemeral=True
    )

    try:

        data = await file.read()

        content = data.decode(
            "utf-8"
        )

        lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

        current_category = None
        current_voice_category = None

        created_categories = 0
        created_text = 0
        created_voice = 0
        skipped = 0
        failed = 0

        for line in lines:

            # -----------------------------------------
            # TEXT CATEGORY
            # -----------------------------------------

            if line.upper().startswith("CATEGORY:"):

                category_name = line.split(
                    ":",
                    1
                )[1].strip()

                existing = discord.utils.get(
                    interaction.guild.categories,
                    name=category_name
                )

                if existing:

                    current_category = existing

                else:

                    try:

                        current_category = await interaction.guild.create_category(
                            category_name,
                            reason="ChannelCat TXT import"
                        )

                        created_categories += 1

                    except Exception:

                        current_category = None
                        failed += 1

                current_voice_category = None

            # -----------------------------------------
            # VOICE CATEGORY
            # -----------------------------------------

            elif line.upper().startswith("VOICECATEGORY:"):

                category_name = line.split(
                    ":",
                    1
                )[1].strip()

                existing = discord.utils.get(
                    interaction.guild.categories,
                    name=category_name
                )

                if existing:

                    current_voice_category = existing

                else:

                    try:

                        current_voice_category = await interaction.guild.create_category(
                            category_name,
                            reason="ChannelCat TXT import"
                        )

                        created_categories += 1

                    except Exception:

                        current_voice_category = None
                        failed += 1

                current_category = None

            # -----------------------------------------
            # TEXT CHANNEL
            # -----------------------------------------

            elif line.upper().startswith("CHANNEL:"):

                channel_name = line.split(
                    ":",
                    1
                )[1].strip()

                existing = discord.utils.get(
                    interaction.guild.text_channels,
                    name=channel_name
                )

                if existing:

                    skipped += 1
                    continue

                try:

                    await interaction.guild.create_text_channel(
                        channel_name,
                        category=current_category,
                        reason="ChannelCat TXT import"
                    )

                    created_text += 1

                except Exception:

                    failed += 1

            # -----------------------------------------
            # VOICE CHANNEL
            # -----------------------------------------

            elif line.upper().startswith("VOICE:"):

                channel_name = line.split(
                    ":",
                    1
                )[1].strip()

                existing = discord.utils.get(
                    interaction.guild.voice_channels,
                    name=channel_name
                )

                if existing:

                    skipped += 1
                    continue

                try:

                    await interaction.guild.create_voice_channel(
                        channel_name,
                        category=current_voice_category,
                        reason="ChannelCat TXT import"
                    )

                    created_voice += 1

                except Exception:

                    failed += 1

        await interaction.followup.send(
            f"""🐱 **ChannelCat Creation Complete**

📁 Categories created: **{created_categories}**
💬 Text channels created: **{created_text}**
🔊 Voice channels created: **{created_voice}**
⏭️ Skipped: **{skipped}**
❌ Failed: **{failed}**""",
            ephemeral=True
        )

    except Exception as e:

        await interaction.followup.send(
            f"❌ Error reading the file:\n`{e}`",
            ephemeral=True
        )


# =========================================================
# DELETE CHANNEL
# =========================================================

@bot.tree.command(
    name="deletechannel",
    description="Delete a channel."
)
async def deletechannel(
    interaction: discord.Interaction,
    channel: discord.abc.GuildChannel
):

    if not await security_check(interaction):
        return

    channel_name = channel.name

    try:

        await channel.delete(
            reason=f"ChannelCat channel deletion by {interaction.user}"
        )

        await interaction.response.send_message(
            f"🗑️ Deleted **{channel_name}**.",
            ephemeral=True
        )

    except Exception as e:

        await interaction.response.send_message(
            f"❌ Failed to delete channel:\n`{e}`",
            ephemeral=True
        )


# =========================================================
# RENAME CHANNEL
# =========================================================

@bot.tree.command(
    name="renamechannel",
    description="Rename a channel."
)
async def renamechannel(
    interaction: discord.Interaction,
    channel: discord.abc.GuildChannel,
    new_name: str
):

    if not await security_check(interaction):
        return

    old_name = channel.name

    try:

        await channel.edit(
            name=new_name,
            reason=f"ChannelCat channel rename by {interaction.user}"
        )

        await interaction.response.send_message(
            f"✅ Renamed **{old_name}** → **{new_name}**.",
            ephemeral=True
        )

    except Exception as e:

        await interaction.response.send_message(
            f"❌ Failed to rename channel:\n`{e}`",
            ephemeral=True
        )


# =========================================================
# LOCK CHANNEL
# =========================================================

@bot.tree.command(
    name="lockchannel",
    description="Lock a text channel so @everyone cannot send messages."
)
async def lockchannel(
    interaction: discord.Interaction,
    channel: discord.TextChannel
):

    if not await security_check(interaction):
        return

    try:

        overwrite = channel.overwrites_for(
            interaction.guild.default_role
        )

        overwrite.send_messages = False

        await channel.set_permissions(
            interaction.guild.default_role,
            overwrite=overwrite,
            reason=f"ChannelCat channel lock by {interaction.user}"
        )

        await interaction.response.send_message(
            f"🔒 Locked {channel.mention}.",
            ephemeral=True
        )

    except Exception as e:

        await interaction.response.send_message(
            f"❌ Failed to lock channel:\n`{e}`",
            ephemeral=True
        )


# =========================================================
# UNLOCK CHANNEL
# =========================================================

@bot.tree.command(
    name="unlockchannel",
    description="Unlock a text channel."
)
async def unlockchannel(
    interaction: discord.Interaction,
    channel: discord.TextChannel
):

    if not await security_check(interaction):
        return

    try:

        overwrite = channel.overwrites_for(
            interaction.guild.default_role
        )

        overwrite.send_messages = None

        await channel.set_permissions(
            interaction.guild.default_role,
            overwrite=overwrite,
            reason=f"ChannelCat channel unlock by {interaction.user}"
        )

        await interaction.response.send_message(
            f"🔓 Unlocked {channel.mention}.",
            ephemeral=True
        )

    except Exception as e:

        await interaction.response.send_message(
            f"❌ Failed to unlock channel:\n`{e}`",
            ephemeral=True
        )


# =========================================================
# SERVER INFO
# =========================================================

@bot.tree.command(
    name="serverinfo",
    description="Show server information."
)
async def serverinfo(
    interaction: discord.Interaction
):

    if not await security_check(interaction):
        return

    guild = interaction.guild

    embed = discord.Embed(
        title="🐱 ChannelCat Server Info",
        description=f"Information about **{guild.name}**",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Server ID",
        value=str(guild.id),
        inline=False
    )

    embed.add_field(
        name="Members",
        value=str(guild.member_count),
        inline=True
    )

    embed.add_field(
        name="Categories",
        value=str(len(guild.categories)),
        inline=True
    )

    embed.add_field(
        name="Text Channels",
        value=str(len(guild.text_channels)),
        inline=True
    )

    embed.add_field(
        name="Voice Channels",
        value=str(len(guild.voice_channels)),
        inline=True
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# =========================================================
# RUN
# =========================================================

if not BOT_TOKEN:

    print("❌ BOT_TOKEN is missing from .env")
    raise SystemExit

bot.run(BOT_TOKEN)