import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

import psycopg2
import random
import string
import os

load_dotenv()

TOKEN=os.getenv("DISCORD_TOKEN")
GUILD_ID=1497847450919239831

intents=discord.Intents.default()
intents.message_content=True

bot=commands.Bot(
    command_prefix="!",
    intents=intents
)

conn=None
cursor=None


colors={
"blue":discord.ButtonStyle.primary,
"green":discord.ButtonStyle.success,
"red":discord.ButtonStyle.danger,
"gray":discord.ButtonStyle.secondary
}


def connect_database():

    global conn
    global cursor

    db=os.getenv("DATABASE_URL")

    if not db:

        print("DATABASE_URL NOT FOUND")
        return

    conn=psycopg2.connect(db)

    cursor=conn.cursor()

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


def generate_random(length):

    chars=string.ascii_uppercase+string.digits

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

        b1=discord.ui.Button(
            label="Enter Key",
            style=colors.get(
                enter_color.lower(),
                discord.ButtonStyle.primary
            )
        )

        b2=discord.ui.Button(
            label="Get Script",
            style=colors.get(
                get_color.lower(),
                discord.ButtonStyle.success
            )
        )

        b3=discord.ui.Button(
            label="Reset HWID",
            style=colors.get(
                reset_color.lower(),
                discord.ButtonStyle.danger
            )
        )

        b1.callback=self.enter_key
        b2.callback=self.get_script
        b3.callback=self.reset_hwid

        self.add_item(b1)
        self.add_item(b2)
        self.add_item(b3)


    async def enter_key(
        self,
        interaction
    ):

        await interaction.response.send_modal(
            KeyModal()
        )


    async def get_script(
        self,
        interaction
    ):

        await interaction.response.send_message(
            "Script soon",
            ephemeral=True
        )


    async def reset_hwid(
        self,
        interaction
    ):

        cursor.execute(
        """
        UPDATE keys
        SET hwid=NULL
        WHERE discord_id=%s
        """,

        (
            str(
                interaction.user.id
            ),
        )
        )

        conn.commit()

        await interaction.response.send_message(
            "✅ HWID Reset",
            ephemeral=True
        )


class KeyModal(
    discord.ui.Modal,
    title="Enter Key"
):


    key=discord.ui.TextInput(
        label="Your Key",
        placeholder="Skid-XXXXX"
    )


    async def on_submit(
        self,
        interaction:discord.Interaction
    ):


        cursor.execute(
        """
        SELECT used
        FROM keys
        WHERE key=%s
        """,

        (
            str(self.key),
        )
        )

        data=cursor.fetchone()


        if not data:

            await interaction.response.send_message(
            "❌ Invalid key",
            ephemeral=True
            )

            return


        if data[0]:

            await interaction.response.send_message(
            "❌ Key already used",
            ephemeral=True
            )

            return


        hwid=str(
            interaction.user.id
        )+"-"+str(
            interaction.guild.id
        )


        cursor.execute(
        """

        UPDATE keys

        SET
        used=%s,
        discord_id=%s,
        hwid=%s

        WHERE key=%s

        """,

        (

        True,
        str(interaction.user.id),
        hwid,
        str(self.key)

        )

        )


        conn.commit()


        await interaction.response.send_message(
        "✅ Key activated",
        ephemeral=True
        )


@bot.event
async def on_ready():

    connect_database()

    guild=discord.Object(
        id=GUILD_ID
    )

    synced=await bot.tree.sync(
        guild=guild
    )

    print(
        f"Synced {len(synced)}"
    )

    print("READY")



@bot.tree.command(
guild=discord.Object(id=GUILD_ID)
)

async def sendpanel(

interaction:discord.Interaction,
title:str,
description:str,
field:str,
enter_color:str="blue",
get_color:str="green",
reset_color:str="red"

):

    embed=discord.Embed(

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
guild=discord.Object(id=GUILD_ID)
)

async def generatekey(

interaction:discord.Interaction,
validate:str,
key:str=None,
prefix:str=None,
length:int=24

):


    allowed=[

    "seconds",
    "hours",
    "days",
    "months",
    "years"

    ]


    validate=validate.lower()


    if validate!="lifetime":

        try:

            amount,unit=validate.split()

            amount=int(amount)

            if unit not in allowed:

                await interaction.response.send_message(
                "❌ only seconds/hours/days/months/years",
                ephemeral=True
                )

                return


        except:

            await interaction.response.send_message(
            "❌ Example: 30 days",
            ephemeral=True
            )

            return



    if key is None:

        key=generate_random(length)


    if prefix:

        key=f"{prefix}-{key}"



    try:

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

    except:

        await interaction.response.send_message(
        "❌ key exists",
        ephemeral=True
        )

        return


    await interaction.response.send_message(

    f"✅ Generated:\n{key}",

    ephemeral=True

    )



@bot.tree.command(
guild=discord.Object(id=GUILD_ID)
)

async def deletekey(

interaction:discord.Interaction,
key:str

):


    cursor.execute(

    """

    DELETE FROM keys
    WHERE key=%s

    """,

    (key,)

    )

    conn.commit()


    await interaction.response.send_message(
    f"Deleted:\n{key}",
    ephemeral=True
    )



@bot.tree.command(
guild=discord.Object(id=GUILD_ID)
)

async def keyslist(
interaction:discord.Interaction
):


    cursor.execute(
    "SELECT key FROM keys LIMIT 20"
    )

    rows=cursor.fetchall()


    if not rows:

        await interaction.response.send_message(
        "No keys",
        ephemeral=True
        )

        return


    text=""


    for row in rows:

        text+=f"{row[0]}\n"


    embed=discord.Embed(

    title="Keys List",
    description=text

    )


    await interaction.response.send_message(
    embed=embed,
    ephemeral=True
    )



@bot.tree.command(
guild=discord.Object(id=GUILD_ID)
)

async def keyinfo(

interaction:discord.Interaction,
key:str

):


    cursor.execute(

    """

    SELECT used,
    discord_id,
    hwid,
    validation

    FROM keys

    WHERE key=%s

    """,

    (key,)

    )


    data=cursor.fetchone()


    if not data:

        await interaction.response.send_message(
        "key not found",
        ephemeral=True
        )

        return


    embed=discord.Embed(
    title="Key Info"
    )


    embed.add_field(
    name="Used",
    value=data[0],
    inline=False
    )

    embed.add_field(
    name="Discord ID",
    value=data[1] or "None",
    inline=False
    )

    embed.add_field(
    name="HWID",
    value=data[2] or "None",
    inline=False
    )

    embed.add_field(
    name="Validation",
    value=data[3],
    inline=False
    )


    await interaction.response.send_message(
    embed=embed,
    ephemeral=True
    )



@bot.tree.command(
guild=discord.Object(id=GUILD_ID)
)

async def userinfo(

interaction:discord.Interaction,
user:discord.Member

):


    cursor.execute(

    """

    SELECT key,validation

    FROM keys

    WHERE discord_id=%s

    """,

    (str(user.id),)

    )


    data=cursor.fetchone()


    embed=discord.Embed(
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
        name="Validation",
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
        name="Validation",
        value="Non-User",
        inline=False
        )


    await interaction.response.send_message(
    embed=embed
    )


bot.run(TOKEN)