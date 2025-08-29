
import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime
import random
import io

DB_FILE = "data.json"

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        db = json.load(f)
else:
    db = {"links": [], "usage": {}}

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

GUILD = discord.Object(id=1234567890) # <-- server id


def get_month_key():
    return datetime.now().strftime("%Y-%m")

def get_limit(member: discord.Member):
    booster_role = discord.utils.get(member.roles, name="booster")
    return 15 if booster_role else 5


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync(guild=GUILD)
        print(f"Synced {len(synced)} commands to guild {GUILD.id}")
    except Exception as e:
        print(e)

@bot.tree.command(name="get", description="Get a link", guild=GUILD)
async def get_link(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    month_key = get_month_key()

    if user_id not in db["usage"]:
        db["usage"][user_id] = {}
    if month_key not in db["usage"][user_id]:
        db["usage"][user_id][month_key] = 0

    limit = get_limit(interaction.user)
    if db["usage"][user_id][month_key] >= limit:
        return await interaction.response.send_message(
            f"You’ve reached your monthly limit of {limit} links.",
            ephemeral=True,
        )

    if not db["links"]:
        return await interaction.response.send_message(
            "No links available. Contact a developer in our server.",
            ephemeral=True,
        )

    link = random.choice(db["links"])
    db["usage"][user_id][month_key] += 1
    save_db()


    try:
        await interaction.user.send(f"Enjoy your link 🥳 : {link}")
        await interaction.response.send_message("a DM has been sent to you with your link!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(
            "Unable to DM, Please make sure DMs are enabled.",
            ephemeral=True
        )

@bot.tree.command(name="add", description="Add link (Admin only)", guild=GUILD)
@app_commands.checks.has_permissions(administrator=True)
async def add_link(interaction: discord.Interaction, url: str):
    db["links"].append(url)
    save_db()
    await interaction.response.send_message(f"Successfully added the link: {url}")




@bot.tree.command(name="list", description="List links (Admin only)", guild=GUILD)
@app_commands.checks.has_permissions(administrator=True)
async def list_links(interaction: discord.Interaction, count: str = "all"):
    if not db["links"]:
        return await interaction.response.send_message("No links are stored.")

    if count.lower() == "all":
        text = "\n".join([f"{i+1}. {l}" for i, l in enumerate(db["links"])])
    else:
        try:
            num = int(count)
            text = "\n".join([f"{i+1}. {l}" for i, l in enumerate(db["links"][:num])])
        except ValueError:
         return await interaction.response.send_message("Invalid command. Use a number or 'all'.")

    await interaction.response.send_message(f"Links:\n{text}")




@bot.tree.command(name="islink", description="Check if link is in the database (alternative to fishing out the link with /list) (Admin only)", guild=GUILD)
@app_commands.checks.has_permissions(administrator=True)
async def fish_links(interaction: discord.Interaction, link: str = "all"):
    if link in db["links"]:
        return await interaction.response.send_message("true")

    if link not in db["links"]:
        await interaction.response.send_message("false")




@bot.tree.command(name="remove", description="Remove a link(Admin only)", guild=GUILD)
@app_commands.checks.has_permissions(administrator=True)
async def remove_link(interaction: discord.Interaction, link: str = "all"):
    if link not in db["links"]:
        return await interaction.response.send_message("link not found")

    db["links"].remove(link)
    save_db()
    await interaction.response.send_message(f"Successfully removed link: {link}")




@bot.tree.command(name="listbulk", description="list links in bulk (Admin only)", guild=GUILD)
@app_commands.checks.has_permissions(administrator=True)
async def bulk_link(interaction: discord.Interaction):
    if not db["links"]:
        return await interaction.response.send_message("no links were found in the database")

    text_data = "\n".join([f"{i+1}. {l}" for i, l in enumerate(db["links"])])

    file = discord.File(io.StringIO(text_data), filename="links.txt")

    await interaction.response.send_message("bulk link request success:", file=file)




@bot.tree.command(name="deletebulk", description="delete link database (Admin only)", guild=GUILD)
@app_commands.checks.has_permissions(administrator=True)
async def bulk_link(interaction: discord.Interaction):
    embed = discord.Embed(
        title="CONFIRM DATABASE DELETION",
        description="By clicking confirm, all links will be deleted and unrecoverable",
        color=discord.Color.red()
    )

    await interaction.response.send_message(embed=embed, view=ConfirmDatabaseDeletionButton())
    



class ConfirmDatabaseDeletionButton(discord.ui.View):
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        db["links"].clear()
        save_db()
        await interaction.message.delete()
        await interaction.response.send_message("The database has been cleared")

class LinkButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Get Link", style=discord.ButtonStyle.green, custom_id="get_link_button")
    async def get_link_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        month_key = get_month_key()

        if user_id not in db["usage"]:
            db["usage"][user_id] = {}
        if month_key not in db["usage"][user_id]:
            db["usage"][user_id][month_key] = 0

        limit = get_limit(interaction.user)
        if db["usage"][user_id][month_key] >= limit:
            return await interaction.response.send_message(
                f"You’ve reached your monthly limit of {limit} links.",
                ephemeral=True,
            )

        if not db["links"]:
            return await interaction.response.send_message(
                "No links available. Contact a developer in our server.",
                ephemeral=True,
            )

        import random
        link = random.choice(db["links"])
        db["usage"][user_id][month_key] += 1
        save_db()

        try:
            await interaction.user.send(f"Enjoy your link 🥳: {link}")
            await interaction.response.send_message("a DM has been sent to you with your link!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(
                "error: couldnt dm",
                ephemeral=True
            )




@bot.tree.command(name="linkchannel", description="Post the link embed with button", guild=GUILD)
@app_commands.checks.has_permissions(administrator=True)
async def link_channel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔗 Link Bot",
        description="Click the button to get your link!\n\n"
                    "Normal users: **5 per month**\n"
                    "Boosters: **15 per month**",
        color=discord.Color.green()
    )
    await interaction.channel.send(embed=embed, view=LinkButton())
    await interaction.response.send_message("its posted go check it out", ephemeral=True)




bot.run("token") # <-- bot token

#made by thekingballin