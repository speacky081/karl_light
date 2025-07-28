import sqlite3
import time
import os
import random
import math
import asyncio
import filetype
import discord as dc
from discord import app_commands
from discord import Color

# Emojis: :white_large_square: :green_square: :blue_square: :purple_square: :orange_square:
# database tables:
# card_templates
# user_tokens (only user id and tokens)
# cards (actual cards that exist. Have ucid)
# one table per player with all their ucids named user_{player_id}

MAX_FILE_SIZE = 5 * 1024 * 1024 # 5MB
ALLOWED_TYPES = {"image/png", "image/jpeg", "image/gif"}

with open("ADMINID.txt", "r", encoding="utf-8") as file:
    ADMINID = int(file.readlines()[0])

def daily_token() -> None:
    '''Give everyone 1 Token'''
    con = sqlite3.connect("tcg.db")
    cur = con.cursor()
    cur.execute("""
        UPDATE user_tokens
        SET tokens = tokens + 1;
    """)
    con.commit()
    con.close()

def choose_miitopia()-> str:
    '''returns a random miitopia role'''
    role = random.choice([
        "Warrior",
        "Imp",
        "Mage",
        "Scientist",
        "Cleric",
        "Tank",
        "Pop Star",
        "Princess",
        "Thief",
        "Flower",
        "Chef",
        "Vampire",
        "Cat",
        "Elf"
    ])
    return role

def choose_murder() -> str:
    '''returns a random murder mistery role'''
    role = random.choice([
        "Leiche",
        "Detektiv",
        "Assistent des Detektivs",
        "Ermittlungsbeamter",
        "Frau des Opfers",
        "Hausmädchen",
        "Gärtner",
        "Täter",
        "Mastermind",
        "Chinamann"
    ])
    return role

def save_card(new_card: dict) -> None:
    '''save a card to the db'''
    con = sqlite3.connect("tcg.db")
    cur = con.cursor()
    cur.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                ucid INTEGER,
                name TEXT,
                hp INTEGER,
                staerke TEXT,
                schwaeche TEXT,
                rarity INTEGER,
                file_path TEXT,
                total_score INTEGER,
                strength TEXT,
                intelligence TEXT,
                murder_role TEXT,
                miitopia_role TEXT
            )
            """)
    cur.execute("INSERT INTO cards VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (new_card["ucid"],
            new_card["name"],
            new_card["hp"],
            new_card["staerke"],
            new_card["schwaeche"],
            new_card["rarity"],
            new_card["image"],
            new_card["total_score"],
            new_card["strength"],
            new_card["intelligence"],
            new_card["murder_role"],
            new_card["miitopia_role"]
            ))
    con.commit()
    con.close()

def assign_card_to_player(ucid: int, player_id: int) -> None:
    '''save a card ucid to a players inventory'''
    con = sqlite3.connect("tcg.db")
    cur = con.cursor()
    cur.execute(f"CREATE TABLE IF NOT EXISTS user_{player_id} (ucid INTEGER)")
    cur.execute(f"INSERT INTO user_{player_id} VALUES (?)", (ucid,))
    con.commit()
    con.close()

def charge_user(user_id: int, cost: int) -> None:
    '''reduce tokens from user'''
    con = sqlite3.connect("tcg.db")
    cur = con.cursor()

    cur.execute(
        "UPDATE user_tokens SET tokens = tokens - ? WHERE id = ?",
        (cost, user_id)
    )
    con.commit()
    con.close()

def create_card(rarity: int) -> int:
    '''saves the card to the db and returns the unique card ID so you can add it to the playerdb'''
    possible_values = {
        1: {
            "strength": ["poor", "decent"],
            "intelligence": ["poor", "decent"]
        },
        2: {
            "strength": ["poor", "decent", "great"],
            "intelligence": ["poor", "decent"]
        },
        3: {
            "strength": ["poor", "decent", "great"],
            "intelligence": ["poor", "decent", "great"]
        },
        4: {
            "strength": ["decent", "great"],
            "intelligence": ["poor", "decent", "great"]
        },
        5: {
            "strength": ["decent", "great"],
            "intelligence": ["decent", "great"]
        }
    }

    con = sqlite3.connect("tcg.db")
    cur = con.cursor()
    cur.execute("""
        SELECT *
        FROM card_templates
        WHERE rarity <= ?
        ORDER BY RANDOM()
        LIMIT 1
    """, (rarity,))
    template = cur.fetchone()
    con.close()
    # unique card ID
    ucid = hash(str(time.time()) + str(template[0]) + str(rarity) + template[1] + template[3] + template[4])

    miitopia_role = choose_miitopia()
    murder_role = choose_murder()

    strength = random.choice(possible_values[rarity]["strength"])
    intelligence = random.choice(possible_values[rarity]["intelligence"])

    total_score = 0
    total_score += math.floor(math.log(template[2])**2)
    total_score += math.floor(math.exp(rarity-1))

    match strength:
        case "poor":
            total_score += 5
        case "decent":
            total_score += 15
        case "great":
            total_score += 45

    match intelligence:
        case "poor":
            total_score += 5
        case "decent":
            total_score += 15
        case "great":
            total_score += 45

    new_card = {
        "name": template[1],
        "hp": template[2],
        "staerke": template[3],
        "schwaeche": template[4],
        "rarity": rarity,
        "image": template[7],
        "total_score": total_score,
        "strength": strength,
        "intelligence": intelligence,
        "murder_role": murder_role,
        "miitopia_role": miitopia_role,
        "ucid": ucid
    }
    save_card(new_card)
    return ucid

def read_card_from_db(ucid: int) -> dict:
    '''reads a card from the db and returns it as dict'''
    con = sqlite3.connect("tcg.db")
    cur = con.cursor()
    cur.execute(f"""
            SELECT
            ucid,
            name,
            hp,
            staerke,
            schwaeche,
            rarity,
            file_path,
            total_score,
            strength,
            intelligence,
            murder_role,
            miitopia_role FROM cards WHERE ucid = ?""", (ucid,))
    card_tuple = cur.fetchone()
    card = {
        "name": card_tuple[1],
        "hp": card_tuple[2],
        "staerke": card_tuple[3],
        "schwaeche": card_tuple[4],
        "rarity": card_tuple[5],
        "image": card_tuple[6],
        "total_score": card_tuple[7],
        "strength": card_tuple[8],
        "intelligence": card_tuple[9],
        "murder_role": card_tuple[10],
        "miitopia_role": card_tuple[11],
        "ucid": ucid
    }
    con.close()
    return card

def create_embed(card: dict) -> tuple[dc.Embed, dc.File]:
    '''create the embed to display to the player'''
    color = {
        1: Color.light_gray(),
        2: Color.brand_green(),
        3: Color.blue(),
        4: Color.purple(),
        5: Color.gold()
    }

    rarity_translation = {
        1: "Normal :star:",
        2: "Ungewöhnlich :star::star:",
        3: "Selten :star::star::star:",
        4: "Episch :star::star::star::star:",
        5: "Legendär :star::star::star::star::star:"
    }

    embed = dc.Embed(
        title=rarity_translation[card["rarity"]],
        color=color[card["rarity"]]
    )
    embed.set_author(name=f"{card['name']}: {card['total_score']}")
    embed.add_field(name="HP", value=card["hp"], inline=True)
    embed.add_field(name="Intelligence", value=card["intelligence"], inline=True)
    embed.add_field(name="Strength", value=card["strength"], inline=True)
    embed.add_field(name="Miitopia Rolle", value=card["miitopia_role"], inline=True)
    embed.add_field(name="Murder Mystery Rolle", value=card["murder_role"], inline=True)
    embed.add_field(name="Stärke", value=card["staerke"])
    embed.add_field(name="Schwäche", value=card["schwaeche"])
    embed.set_footer(text=f'id: {card["ucid"]}')

    filename = os.path.basename(card["image"])
    dc_file = dc.File(fp=card["image"], filename=filename)
    embed.set_image(url=f"attachment://{filename}")
    embed.set_thumbnail(url=f"attachment://{filename}")

    return embed, dc_file

class ShopView(dc.ui.View,):
    '''
    Create view with buttons.
    One Button per Boosterpack rarity.
    Buttons check if the user has enough money to buy the pack
    '''

    def __init__(self, owner_id: int, *, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.owner_id = owner_id

    @dc.ui.button(label="normal", style=dc.ButtonStyle.secondary, emoji="⬜")
    async def normal_button_callback(self, interaction: dc.Interaction, button):
        '''generate a normal booster pack'''
        await interaction.response.defer()

        if interaction.user.id != self.owner_id:
            await interaction.followup.send_message("Du hast den Shop nicht bestellt!", ephemeral=True)
            return

        for b in self.children:
            b.disabled = True
        await interaction.message.edit(view=self)

        steps = random.randint(8,12)

        # make the indicator for the roulette wheel
        ticker = ""
        for _ in range(5):
            ticker += ":white_large_square:"
        ticker += ":arrow_down_small:"

        for _ in range(5):
            ticker += ":white_large_square:"

        ticker_msg = await interaction.followup.send(ticker, wait=True)

        charge_user(interaction.user.id, 1)

        #now make the actual roulette wheel
        roulette_list = []
        # wheel will be a list of numbers but translated as colors for dc
        translations = {
            1: ":white_large_square:",
            2: ":green_square:",
            3: ":blue_square:",
            4: ":purple_square:",
            5: ":orange_square:"
        }
        for _ in range(11):
            rarity = random.randint(1, 100)
            if rarity < 70:
                roulette_list.append(1)
            elif rarity < 85:
                roulette_list.append(2)
            elif rarity < 95:
                roulette_list.append(3)
            elif rarity < 98:
                roulette_list.append(4)
            else:
                roulette_list.append(5)

        #send roulette wheel and update it steps # of times
        wheel_str = "".join(translations[i] for i in roulette_list)
        await ticker_msg.edit(content=ticker + "\n" + wheel_str)
        for j in range(steps):
            first = roulette_list.pop(0)
            roulette_list.append(first)
            wheel_str = "".join(translations[i] for i in roulette_list)
            await ticker_msg.edit(content=ticker + "\n" + wheel_str)
            await asyncio.sleep((j**2)/64)

        rarity = roulette_list[5]
        ucid = create_card(rarity)
        assign_card_to_player(ucid, interaction.user.id)
        card = read_card_from_db(ucid)
        embed, dc_file = create_embed(card)
        await interaction.followup.send(embed=embed, file=dc_file)

    @dc.ui.button(label="ungewöhnlich", style=dc.ButtonStyle.secondary, emoji="🟩")
    async def uncommon_button_callback(self, interaction: dc.Interaction, button):
        '''generate an uncommon booster pack'''
        await interaction.response.defer()
        if interaction.user.id != self.owner_id:
            await interaction.followup.send_message("Du hast den Shop nicht bestellt!", ephemeral=True)
            return

        for b in self.children:
            b.disabled = True
        await interaction.message.edit(view=self)

        steps = random.randint(8,12)

        # make the indicator for the roulette wheel
        ticker = ""
        for _ in range(5):
            ticker += ":green_square:"
        ticker += ":arrow_down_small:"

        for _ in range(5):
            ticker += ":green_square:"

        ticker_msg = await interaction.followup.send(ticker, wait=True)

        charge_user(interaction.user.id, 3)

        #now make the actual roulette wheel
        roulette_list = []
        # wheel will be a list of numbers but translated as colors for dc
        translations = {
            1: ":white_large_square:",
            2: ":green_square:",
            3: ":blue_square:",
            4: ":purple_square:",
            5: ":orange_square:"
        }
        for _ in range(11):
            rarity = random.randint(1, 100)
            if rarity < 70:
                roulette_list.append(2)
            elif rarity < 85:
                roulette_list.append(3)
            elif rarity < 95:
                roulette_list.append(4)
            else:
                roulette_list.append(5)

        #send roulette wheel and update it steps # of times
        wheel_str = "".join(translations[i] for i in roulette_list)
        await ticker_msg.edit(content=ticker + "\n" + wheel_str)
        for j in range(steps):
            first = roulette_list.pop(0)
            roulette_list.append(first)
            wheel_str = "".join(translations[i] for i in roulette_list)
            await ticker_msg.edit(content=ticker + "\n" + wheel_str)
            await asyncio.sleep((j**2)/64)

        rarity = roulette_list[5]
        ucid = create_card(rarity)
        assign_card_to_player(ucid, interaction.user.id)
        card = read_card_from_db(ucid)
        embed, dc_file = create_embed(card)
        await interaction.followup.send(embed=embed, file=dc_file)

    @dc.ui.button(label="selten", style=dc.ButtonStyle.secondary, emoji="🟦")
    async def rare_button_callback(self, interaction: dc.Interaction, button):
        '''generate a rare booster pack'''
        await interaction.response.defer()
        if interaction.user.id != self.owner_id:
            await interaction.followup.send_message("Du hast den Shop nicht bestellt!", ephemeral=True)
            return

        for b in self.children:
            b.disabled = True
        await interaction.message.edit(view=self)

        steps = random.randint(8,12)

        # make the indicator for the roulette wheel
        ticker = ""
        for _ in range(5):
            ticker += ":blue_square:"
        ticker += ":arrow_down_small:"

        for _ in range(5):
            ticker += ":blue_square:"

        ticker_msg = await interaction.followup.send(ticker, wait=True)

        charge_user(interaction.user.id, 5)

        #now make the actual roulette wheel
        roulette_list = []
        # wheel will be a list of numbers but translated as colors for dc
        translations = {
            1: ":white_large_square:",
            2: ":green_square:",
            3: ":blue_square:",
            4: ":purple_square:",
            5: ":orange_square:"
        }
        for _ in range(11):
            rarity = random.randint(1, 100)
            if rarity < 70:
                roulette_list.append(3)
            elif rarity < 85:
                roulette_list.append(4)
            else:
                roulette_list.append(5)

        #send roulette wheel and update it steps # of times
        wheel_str = "".join(translations[i] for i in roulette_list)
        await ticker_msg.edit(content=ticker + "\n" + wheel_str)
        for j in range(steps):
            first = roulette_list.pop(0)
            roulette_list.append(first)
            wheel_str = "".join(translations[i] for i in roulette_list)
            await ticker_msg.edit(content=ticker + "\n" + wheel_str)
            await asyncio.sleep((j**2)/64)

        rarity = roulette_list[5]
        ucid = create_card(rarity)
        assign_card_to_player(ucid, interaction.user.id)
        card = read_card_from_db(ucid)
        embed, dc_file = create_embed(card)
        await interaction.followup.send(embed=embed, file=dc_file)

class Tcg(dc.ext.commands.Cog):
    '''The Cog for the TCG'''
    def __init__(self, bot):
        self.bot = bot

    tcg = app_commands.Group(
        name="tcg",
        description="Gruppe an Commands für das TCG"
    )

    @tcg.command(
        name="add",
        description="(ADMIN ONLY) Füge eine Karte in das TCG hinzu"
        )
    @app_commands.describe(
        name="Name der Karte",
        hp="Lebenspunkte der Karte",
        staerke="Wogegen die Karte stark ist",
        schwaeche="Wogegen die Karte Schwach ist"
    )
    async def add_card(
        self,
        interaction: dc.Interaction,
        name: str,
        hp: app_commands.Range[int, 1,100],
        staerke: str,
        schwaeche: str,
        rarity: app_commands.Range[int, 1,5]):
        '''Add a card to the database. Rarity is the number given or higher'''
        if not interaction.user.id == ADMINID:
            await interaction.response.send_message("Du hast nicht die Rechte diesen Befehl auszuführen!")
            return
        if len(name) > 30:
            await interaction.response.send_message("Der Name ist zu lang (max: 30)", ephemeral=True)
            return
        if len(name) < 3:
            await interaction.response.send_message("Der Name ist zu kurz (min: 2)", ephemeral=True)
            return
        if len(staerke) > 30:
            await interaction.response.send_message("Die Stärke ist zu lang (max: 30)", ephemeral=True)
            return
        if len(staerke) < 1:
            await interaction.response.send_message("Die Stärke ist zu kurz (min: 1)", ephemeral=True)
            return
        if len(schwaeche) > 30:
            await interaction.response.send_message("Die Schwäche ist zu lang (max: 30)", ephemeral=True)
            return
        if len(schwaeche) < 1:
            await interaction.response.send_message("Die Schwäche ist zu kurz (min: 1)", ephemeral=True)
            return
        
        creator = interaction.user.id

        await interaction.response.send_message(
            "Bitte sende innerhalb von 60 Sekunden ein Bild für die Karte in diesen Chat",
            ephemeral=True
            )

        def check(msg):
            return (
                msg.author == interaction.user and
                msg.channel == interaction.channel and
                msg.attachments
            )

        try:
            msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            image = msg.attachments[0]

            # Size check
            if image.size > MAX_FILE_SIZE:
                await interaction.followup.send("Das Bild ist zu groß (max: 5Mb)", ephemeral=True)
                return

            # Type check
            data = await image.read()
            kind = filetype.guess(data)
            if kind is None or kind.mime not in ALLOWED_TYPES:
                await interaction.followup.send("Invalides Bildformat. Bitte nutze jpeg, png oder gif", ephemeral=True)
                return

            ext = kind.extension

            # Save image
            os.makedirs("TCG_images", exist_ok=True)
            file_path = f"TCG_images/{name}_{str(hash(time.time()))}{str(hash(name))}.{ext}"
            with open(file_path, "wb") as f:
                f.write(data)

            con = sqlite3.connect("tcg.db")
            cur = con.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS card_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                hp INTEGER,
                staerke TEXT,
                schwaeche TEXT,
                rarity INTEGER,
                creator INTEGER,
                file_path TEXT
            )
            """)

            cur.execute(
                """
                INSERT INTO card_templates
                (name, hp, staerke, schwaeche, rarity, creator, file_path)
                VALUES
                (?, ?, ?, ?, ?, ?, ?)
                """,
                (name, hp, staerke, schwaeche, rarity, creator, file_path)
            )
            con.commit()
            con.close()

            await interaction.followup.send(f"Card `{name}` added with image!", ephemeral=True)

        except asyncio.TimeoutError:
            await interaction.followup.send("Timed out waiting for an image.", ephemeral=True)

    @tcg.command(
        name="register",
        description="Lege ein Token-Konto an um Boosterpacks kaufen zu können"
    )
    async def register(self, interaction: dc.Interaction):
        '''Let user register a to get tokens daily'''
        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id

        con = sqlite3.connect("tcg.db")
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_tokens (
            id INTEGER,
            tokens INTEGER
        )
        """)

        cur.execute("SELECT 1 FROM user_tokens WHERE id = ?", (user_id,))
        result = cur.fetchone()

        if not result:
            cur.execute("INSERT INTO user_tokens VALUES (?, ?)", (user_id, 4))
            con.commit()
            con.close()
            await interaction.followup.send("Du hast erfolgreich ein Konto eröffnet. Ab jetzt bekommst du täglich ein Token!")
        else:
            await interaction.followup.send("Du hast schon ein Konto")

    @tcg.command(
        name="shop",
        description="Öffne den Kartenpackshop"
    )
    async def shop(self, interaction: dc.Interaction):
        '''display a shop embed with buttons to user to enable them to buy cards'''
        await interaction.response.defer()

        user_id = interaction.user.id

        con = sqlite3.connect("tcg.db")
        cur = con.cursor()

        cur.execute("SELECT tokens FROM user_tokens WHERE id = ?", (user_id,))
        row = cur.fetchone()
        player_tokens = row[0] if row else 0
        cur.close()

        view = ShopView(user_id)

        for btn in view.children:
            if btn.label == "normal" and player_tokens < 1:
                btn.disabled = True
            elif btn.label == "ungewöhnlich" and player_tokens < 3:
                btn.disabled = True
            elif btn.label == "selten" and player_tokens < 5:
                btn.disabled = True

        embed = dc.Embed(
            title="Booster‑Pack Shop",
            description=f"Deine Token: `{player_tokens}`",
            color=dc.Color.blurple()
        )
        await interaction.followup.send(embed=embed, view=view)

    @tcg.command(
        name="inventar",
        description="lass dir eine kurze übersicht über deine karten senden"
    )
    async def inventory(self, interaction: dc.Interaction):
        '''send a string with most important properties of cards'''
        await interaction.response.defer()

        rarity_translation = {
            1: "Normal :star:",
            2: "Ungewöhnlich :star::star:",
            3: "Selten :star::star::star:",
            4: "Episch :star::star::star::star:",
            5: "Legendär :star::star::star::star::star:"
        }

        user_id = interaction.user.id

        cards = []

        con = sqlite3.connect("tcg.db")
        cur = con.cursor()
        cur.execute(f"SELECT ucid FROM user_{user_id}")
        card_ucids = cur.fetchall()
        for ucid in card_ucids:
            cards.append(read_card_from_db(ucid[0]))

        inventory_string = ""
        for card in cards:
            inventory_string += f"{card['name']}: {rarity_translation[card['rarity']]}; {card['total_score']}. id: {card['ucid']}\n"
            if len(inventory_string) > 1500 and len(inventory_string) < 2000:
                await interaction.followup.send(inventory_string)
                inventory_string = ""
        await interaction.followup.send(inventory_string)

    @tcg.command(
        name="show",
        description="gib eine ID einer deiner Karten an um sie dir anzeigen zu lassen"
    )
    async def show(self, interaction: dc.Interaction, ucid_str: int):
        '''Let the user display one of their cards'''

        ucid = int(ucid_str)
        user_id = interaction.user.id

        con = sqlite3.connect("tcg.db")
        cur = con.cursor()
        cur.execute(f"SELECT 1 FROM user_{user_id} WHERE ucid = {ucid}")
        result = cur.fetchone()

        if not result:
            await interaction.response.send_message("Du besitzt diese Karte nicht")
            return

        con.close()

        card = read_card_from_db(ucid)

        embed, dc_file = create_embed(card)
        await interaction.response.send_message(embed=embed, file=dc_file)
