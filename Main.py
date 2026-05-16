import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1497847450919239831

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

colors = {
    "blue": discord.ButtonStyle.primary,
    "green": discord.ButtonStyle.success,
    "red": discord.ButtonStyle.danger,
    "gray": discord.ButtonStyle.secondary
}


class Panel(discord.ui.View):

    def __init__(
        self,
        enter_color="blue",
        get_color="green",
        reset_color="red"
    ):

        super().__init__(timeout=None)

        enter = discord.ui.Button(
            label="Enter Key",
            style=colors.get(
                enter_color.lower(),
                discord.ButtonStyle.primary
            )
        )

        script = discord.ui.Button(
            label="Get Script",
            style=colors.get(
                get_color.lower(),
                discord.ButtonStyle.success
            )
        )

        reset = discord.ui.Button(
            label="Reset HWID",
            style=colors.get(
                reset_color.lower(),
                discord.ButtonStyle.danger
            )
        )

        enter.callback = self.enter_click
        script.callback = self.script_click
        reset.callback = self.reset_click

        self.add_item(enter)
        self.add_item(script)
        self.add_item(reset)

    async def enter_click(self, interaction):

        await interaction.response.send_message(
            "Введите ключ",
            ephemeral=True
        )

    async def script_click(self, interaction):

        await interaction.response.send_message(
            "loadstring(game:HttpGet('URL'))()",
            ephemeral=True
        )

    async def reset_click(self, interaction):

        await interaction.response.send_message(
            "HWID reset requested",
            ephemeral=True
        )


@bot.event
async def on_ready():

    guild = discord.Object(
        id=GUILD_ID
    )

    synced = await bot.tree.sync(
        guild=guild
    )

    print(f"Synced {len(synced)} commands")
    print("================")
    print(bot.user)
    print("READY")
    print("================")


@bot.tree.command(
    name="sendpanel",
    description="Create panel",
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
        description=description,
        color=discord.Color.blue()
    )

    embed.set_footer(
        text=field
    )

    await interaction.response.send_message(
        "Панель Создана",
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


bot.run(TOKEN)