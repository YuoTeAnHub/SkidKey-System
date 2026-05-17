import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime, timedelta

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
    validation TEXT,
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    expired TEXT

    )

    """)

    conn.commit()

    for col, coltype in [("created_at", "TIMESTAMP"), ("expires_at", "TIMESTAMP"), ("expired", "TEXT")]:

        cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='keys'
        AND column_name=%s
        """,
        (col,)
        )

        if not cursor.fetchone():

            cursor.execute(
            f"ALTER TABLE keys ADD COLUMN {col} {coltype}"
            )

            print(f"Added column: {col}")

    conn.commit()

    print("DATABASE CONNECTED")


def generate_random(length):

    chars=string.ascii_uppercase+string.digits

    return ''.join(
        random.choice(chars)
        for i in range(length)
    )


@tasks.loop(seconds=30)
async def expire_keys():

    if cursor is None:
        return

    try:

        cursor.execute(
        """

        SELECT
        key,
        discord_id

        FROM keys

        WHERE
        expires_at IS NOT NULL
        AND expires_at<=NOW()
        AND used=TRUE

        """

        )

        rows=cursor.fetchall()

        for row in rows:

            key=row[0]
            user_id=row[1]

            try:

                user=await bot.fetch_user(
                int(user_id)
                )

                await user.send(
                f"❌ Ваш ключ закончился:\n{key}"
                )

            except:
                pass


            cursor.execute(
            """

            UPDATE keys

            SET

            used=%s,
            discord_id=%s,
            hwid=%s,
            expires_at=%s,
            expired=%s

            WHERE key=%s

            """,

            (

            False,
            None,
            None,
            None,
            "Yes",
            key

            )

            )

        conn.commit()

    except Exception as e:

        conn.rollback()

        print(f"expire_keys error: {e}")


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

        cursor.execute(
        """
        SELECT key
        FROM keys
        WHERE
        discord_id=%s
        AND used=TRUE
        AND expired IS NULL
        """,
        (str(interaction.user.id),)
        )

        data=cursor.fetchone()

        if not data:

            await interaction.response.send_message(
            "❌ Reedem Key To Get Script !",
            ephemeral=True
            )

            return

        user_key=data[0]

        script=(
            f'getgenv().G={{}}\n'
            f'G.Key="{user_key}"\n\n'
            f'loadstring(game:HttpGet("https://raw.githubusercontent.com/YuoTeAnHub/SkidScriptLoader/refs/heads/main/Loader.lua"))()'
        )

        await interaction.response.send_message(
        f"```lua\n{script}\n```",
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
        SELECT used,expires_at
        FROM keys
        WHERE key=%s
        """,

        (
            self.key.value,
        )
        )

        data=cursor.fetchone()


        if not data:

            await interaction.response.send_message(
            "❌ Invalid key",
            ephemeral=True
            )

            return

        expire=data[1]

        if expire:

            if datetime.now()>expire:

                await interaction.response.send_message(
                "❌ Key Expired",
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
        self.key.value

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

    if not expire_keys.is_running():

        expire_keys.start()

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

    created=datetime.now()

    expires=None

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

            if unit=="seconds":
                expires=created+timedelta(seconds=amount)

            elif unit=="hours":
                expires=created+timedelta(hours=amount)

            elif unit=="days":
                expires=created+timedelta(days=amount)

            elif unit=="months":
                expires=created+timedelta(days=amount*30)

            elif unit=="years":
                expires=created+timedelta(days=amount*365)


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


    cursor.execute(
    """
    SELECT key
    FROM keys
    WHERE key=%s
    """,
    (key,)
    )

    exists=cursor.fetchone()

    if exists:

        await interaction.response.send_message(
        "❌ key exists",
        ephemeral=True
        )

        return


    cursor.execute(
    """
    INSERT INTO keys
    (
    key,
    used,
    discord_id,
    hwid,
    validation,
    created_at,
    expires_at
    )

    VALUES(%s,%s,%s,%s,%s,%s,%s)
    """,

    (

    key,
    False,
    None,
    None,
    validate,
    created,
    expires

    )
    )

    conn.commit()


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
    validation,
    expired

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

    embed.add_field(
    name="Expired",
    value=data[4] or "NULL",
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

from flask import Flask, request, jsonify
from threading import Thread
import os

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "status":"online",
        "name":"Skid API"
    })

@app.route("/check")
def check():

    global cursor

    if cursor is None:
        return jsonify({
            "valid":False
        })

    key=request.args.get("key")

    if not key:
        return jsonify({
            "valid":False
        })

    cursor.execute(
    """
    SELECT
    used,
    expired
    FROM keys
    WHERE key=%s
    """,
    (key,)
    )

    data=cursor.fetchone()

    if not data:
        return jsonify({
            "valid":False
        })

    used=data[0]
    expired=data[1]

    if expired=="Yes":
        return jsonify({
            "valid":False
        })

    if used:
        return jsonify({
            "valid":True
        })

    return jsonify({
        "valid":False
    })


def run_api():

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                8080
            )
        )
    )


Thread(
    target=run_api,
    daemon=True
).start()

bot.run(TOKEN)