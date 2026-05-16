import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import json
import random
import string

load_dotenv()

TOKEN=os.getenv("DISCORD_TOKEN")
GUILD_ID=1497847450919239831

intents=discord.Intents.default()
intents.message_content=True

bot=commands.Bot(
    command_prefix="!",
    intents=intents
)

colors={
    "blue":discord.ButtonStyle.primary,
    "green":discord.ButtonStyle.success,
    "red":discord.ButtonStyle.danger,
    "gray":discord.ButtonStyle.secondary
}


def load_keys():

    try:

        with open(
            "data/keys.json",
            "r",
            encoding="utf8"
        ) as f:

            return json.load(f)

    except:

        return {
            "keys":[]
        }


def save_keys(data):

    with open(
        "data/keys.json",
        "w",
        encoding="utf8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4
        )


def load_users():

    try:

        with open(
            "data/users.json",
            "r",
            encoding="utf8"
        ) as f:

            return json.load(f)

    except:

        return {
            "users":[]
        }


def generate_random(length):

    chars=string.ascii_uppercase+string.digits

    result=''.join(
        random.choice(chars)
        for i in range(length)
    )

    return result


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

        b1.callback=self.enter_click
        b2.callback=self.script_click
        b3.callback=self.reset_click

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

    guild=discord.Object(
        id=GUILD_ID
    )

    synced=await bot.tree.sync(
        guild=guild
    )

    print(
        f"Synced {len(synced)} commands"
    )

    print(bot.user)
    print("READY")


@bot.tree.command(
    guild=discord.Object(
        id=GUILD_ID
    )
)
async def sendpanel(
    interaction:discord.Interaction,
    title:str,
    description:str,
    field:str,
    enter_color:str,
    get_color:str,
    reset_color:str
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
    guild=discord.Object(
        id=GUILD_ID
    )
)
async def generatekey(
    interaction:discord.Interaction,
    validate:str,
    key:str=None,
    prefix:str=None,
    length:int=24
):

    db=load_keys()

    if key is None:

        key=generate_random(
            length
        )

    if prefix:

        key=f"{prefix}-{key}"

    db["keys"].append({

        "key":key,
        "used":False,
        "discord_id":None,
        "hwid":None,
        "validation":validate
    })

    save_keys(
        db
    )

    embed=discord.Embed(
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
    interaction:discord.Interaction,
    user:discord.Member
):

    db=load_keys()

    found=None

    for x in db["keys"]:

        if str(
            x["discord_id"]
        )==str(
            user.id
        ):

            found=x

    embed=discord.Embed(
        title="User Info"
    )

    embed.add_field(
        name="Discord ID",
        value=user.id,
        inline=False
    )

    if found:

        embed.add_field(
            name="User Key",
            value=found["key"],
            inline=False
        )

        embed.add_field(
            name="Key Validation",
            value=found["validation"],
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