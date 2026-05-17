import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

import os
import json
import random
import string
import psycopg2

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1497847450919239831

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

conn = None
cursor = None

colors = {
    "blue": discord.ButtonStyle.primary,
    "green": discord.ButtonStyle.success,
    "red": discord.ButtonStyle.danger,
    "gray": discord.ButtonStyle.secondary
}


def connect_database():
    global conn
    global cursor

    try:

        db_url = os.getenv("DATABASE_URL")

        if not db_url:
            print("DATABASE_URL NOT FOUND")
            return False

        conn = psycopg2.connect(
            db_url
        )

        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS keys(
            id SERIAL PRIMARY KEY,
            key TEXT UNIQUE,
            used BOOLEAN,
            discord_id TEXT,
            hwid TEXT,
            validation TEXT
        )
        """)

        conn.commit()

        print("DATABASE CONNECTED")
        print("KEY TABLE CREATED")

        return True

    except Exception as e:

        print("DATABASE ERROR:")
        print(e)

        return False


def generate_random(length):

    chars = string.ascii_uppercase + string.digits

    return ''.join(
        random.choice(chars)
        for i in range(length)
    )


class Panel(discord.ui.View):

    def __init__(
        self,
        enter_color="blue",
        get_color="green",
        reset_color="red"
    ):

        super().__init__(timeout=None)

        b1 = discord.ui.Button(
            label="Enter Key",
            style=colors.get(
                enter_color.lower(),
                discord.ButtonStyle.primary
            )
        )

        b2 = discord.ui.Button(
            label="Get Script",
            style=colors.get(
                get_color.lower(),
                discord.ButtonStyle.success
            )
        )

        b3 = discord.ui.Button(
            label="Reset HWID",
            style=colors.get(
                reset_color.lower(),
                discord.ButtonStyle.danger
            )
        )

        b1.callback = self.enter_click
        b2.callback = self.script_click
        b3.callback = self.reset_click

        self.add_item(b1)
        self.add_item(b2)
        self.add_item(b3)

    async def enter_click(
        self,
        interaction
    ):

        await interaction.response.send_message(
            "Enter Key system soon",
            ephemeral=True
        )

    async def script_click(
        self,
        interaction
    ):

        await interaction.response.send_message(
            "Script soon",
            ephemeral=True
        )

    async def reset_click(
        self,
        interaction
    ):

        await interaction.response.send_message(
            "HWID reset soon",
            ephemeral=True
        )


@bot.event
async def on_ready():

    connect_database()

    guild = discord.Object(
        id=GUILD_ID
    )

    synced = await bot.tree.sync(
        guild=guild
    )

    print(f"Synced {len(synced)} commands")
    print(bot.user)
    print("READY")


@bot.tree.command(
    guild=discord.Object(
        id=GUILD_ID
    )
)
async def sendpanel(
    interaction: discord.Interaction,
    title: str,
    description: str,
    field: str,
    enter_color: str,
    get_color: str,
    reset_color: str
):

    embed = discord.Embed(
        title=title,
        description=description
    )

    embed.set_footer(
        text=field
    )

    await interaction.response.send_message(
        "✅ Панель создана",
        ephemeral=True
    )

    await interaction.channel.send(
        embed=embed,
        view=Panel(
            enter_color,
            get_color,
            reset_color
        )
    )


@bot.tree.command(
    guild=discord.Object(
        id=GUILD_ID
    )
)
async def generatekey(
    interaction: discord.Interaction,
    validate: str,
    key: str = None,
    prefix: str = None,
    length: int = 24
):

    global cursor
    global conn

    if key is None:

        key = generate_random(
            length
        )

    if prefix:

        key = f"{prefix}-{key}"

    cursor.execute(
        """
        INSERT INTO keys
        (key,used,discord_id,hwid,validation)
        VALUES(%s,%s,%s,%s,%s)
        """,
        (
            key,
            False,
            None,
            None,
            validate
        )
    )

    conn.commit()

    embed = discord.Embed(
        title="Key Generated",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Key",
        value=key,
        inline=False
    )

    embed.add_field(
        name="Validation",
        value=validate
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


@bot.tree.command(
    guild=discord.Object(
        id=GUILD_ID
    )
)
async def userinfo(
    interaction: discord.Interaction,
    user: discord.Member
):

    cursor.execute(
        """
        SELECT key,validation
        FROM keys
        WHERE discord_id=%s
        """,
        (
            str(user.id),
        )
    )

    data = cursor.fetchone()

    embed = discord.Embed(
        title="User Info"
    )

    embed.add_field(
        name="Discord ID",
        value=user.id,
        inline=False
    )

    if data:

        embed.add_field(
            name="User Key",
            value=data[0],
            inline=False
        )

        embed.add_field(
            name="Key Validation",
            value=data[1],
            inline=False
        )

    else:

        embed.add_field(
            name="User Key",
            value="Non-User",
            inline=False
        )

        embed.add_field(
            name="Key Validation",
            value="Non-User",
            inline=False
        )

    await interaction.response.send_message(
        embed=embed
    )


bot.run(TOKEN)