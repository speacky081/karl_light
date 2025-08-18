"""
Provide minigames for players to win tokens for the tcg
"""

import io
import random
import os
import time
from datetime import datetime
import sqlite3
from PIL import Image
import discord as dc

rotation_state = {"rot":0, "zom":0, "path":""}
target_state = {"rot":0, "zom":0, "path":""}
rotation_player_group = {}
rotation_player_value = {}
last_zoom = 8
last_rot = 8


translations = {
    "zom":"Zoom",
    "rot":"Rotation"
}

def path_to_random_card() -> str:
    """Return the path to a non-gif image of a card that has already been drawn"""
    con = sqlite3.connect("tcg.db")
    cur = con.cursor()

    cur.execute("""
        SELECT DISTINCT file_path FROM cards
    """)
    paths = [row[0] for row in cur.fetchall()]

    con.close()

    path = random.choice(paths)

    if ".gif" in path:
        path = path_to_random_card()

    return path

class RotateView(dc.ui.View):
    """Attach Buttons for Rotating"""

    def __init__(self, owner_id: int, *, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.owner_id = owner_id
        self.message = None

    async def on_timeout(self):
        """Disable all buttons after timeout"""
        for item in self.children:
            item.disabled = True
        if self.message:  # only edit if message is set
            await self.message.edit(view=self)

    @dc.ui.button(label="links", style=dc.ButtonStyle.secondary, emoji="◀️")
    async def left_button_callback(self, interaction: dc.Interaction, button):
        """Rotate image left by amount based on player at random"""
        user_id = interaction.user.id

        if self.owner_id != user_id:
            await interaction.response.send_message("Das ist nicht dein Kontrollpanel!", ephemeral=True)
            return

        await interaction.response.defer()

        for b in self.children:
            b.disabled = True
        await interaction.message.edit(view=self)

        if user_id in rotation_player_value:
            amount = rotation_player_value[user_id]
            rotation_state["rot"] += amount
            rview = RotateView(user_id)
            await interaction.followup.send(f"<@{user_id}> dreht das Bild um `{amount*10}` Grad nach links")
            button_msg = await interaction.followup.send(f"Hier kannst du weitermachen <@{user_id}>", view=rview)
            rview.message = button_msg
        else:
            cview = ChallengeView(user_id)
            button_msg = await interaction.followup.send("Du bist noch nicht in der Challenge angemeldet", view=cview, ephemeral=True)
            cview.message = button_msg

    @dc.ui.button(label="rechts", style=dc.ButtonStyle.secondary, emoji="▶️")
    async def right_button_callback(self, interaction: dc.Interaction, button):
        """Rotate image left by amount based on player at random"""
        user_id = interaction.user.id

        if self.owner_id != user_id:
            await interaction.response.send_message("Das ist nicht dein Kontrollpanel!", ephemeral=True)
            return

        await interaction.response.defer()

        for b in self.children:
            b.disabled = True
        await interaction.message.edit(view=self)

        if user_id in rotation_player_value:
            amount = rotation_player_value[user_id]
            rotation_state["rot"] -= amount
            rview = RotateView(user_id)
            await interaction.followup.send(f"<@{user_id}> dreht das Bild um `{amount*10}` Grad nach rechts")
            button_msg = await interaction.channel.send(f"Hier kannst du weitermachen <@{user_id}>", view=rview)
            rview.message = button_msg
        else:
            cview = ChallengeView(user_id)
            button_msg = await interaction.followup.send("Du bist noch nicht in der Challenge angemeldet", view=cview, ephemeral=True)
            cview.message = button_msg

class ZoomView(dc.ui.View):
    """Attach Buttons for Zooming"""

    def __init__(self, owner_id: int, *, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.owner_id = owner_id
        self.message = None

    async def on_timeout(self):
        """Disable all buttons after timeout"""
        for item in self.children:
            item.disabled = True
        if self.message:  # only edit if message is set
            await self.message.edit(view=self)

    @dc.ui.button(label="+", style=dc.ButtonStyle.secondary, emoji="🔍")
    async def plus_button_callback(self, interaction: dc.Interaction, button):
        """Rotate image left by amount based on player at random"""
        user_id = interaction.user.id

        if self.owner_id != user_id:
            await interaction.response.send_message("Das ist nicht dein Kontrollpanel!", ephemeral=True)
            return

        await interaction.response.defer()

        for b in self.children:
            b.disabled = True
        await interaction.message.edit(view=self)

        if user_id in rotation_player_value:
            amount = rotation_player_value[user_id]
            rotation_state["zom"] += amount
            zview = ZoomView(user_id)
            await interaction.followup.send(f"<@{user_id}> zoomt das Bild um den Faktor `{amount}`")
            button_msg = await interaction.channel.send(f"Hier kannst du weitermachen <@{user_id}>", view=zview)
            zview.message = button_msg
        else:
            cview = ChallengeView(user_id)
            button_msg = await interaction.followup.send("Du bist noch nicht in der Challenge angemeldet", view=cview, ephemeral=True)
            cview.message = button_msg

    @dc.ui.button(label="-", style=dc.ButtonStyle.secondary, emoji="🔎")
    async def minus_button_callback(self, interaction: dc.Interaction, button):
        """Rotate image left by amount based on player at random"""
        user_id = interaction.user.id

        if self.owner_id != user_id:
            await interaction.response.send_message("Das ist nicht dein Kontrollpanel!", ephemeral=True)
            return

        await interaction.response.defer()

        for b in self.children:
            b.disabled = True
        await interaction.message.edit(view=self)

        if user_id in rotation_player_value:
            amount = rotation_player_value[user_id]
            zview = ZoomView(user_id)
            if rotation_state["zom"] - amount < 0:
                await interaction.followup.send("Du kannst nicht weiter rauszoomen")
                button_msg = await interaction.channel.send(f"Hier kannst du weitermachen <@{user_id}>", view=zview)
            else:
                rotation_state["zom"] -= amount
                await interaction.followup.send(f"<@{user_id}> zoomt das Bild um den Faktor `-{amount}`")
                button_msg = await interaction.channel.send(f"Hier kannst du weitermachen <@{user_id}>", view=zview)
            zview.message = button_msg
        else:
            cview = ChallengeView(user_id)
            button_msg = await interaction.followup.send("Du bist noch nicht in der Challenge angemeldet", view=cview, ephemeral=True)
            cview.message = button_msg

class ChallengeView(dc.ui.View):
    """Attach buttons to choose team"""

    def __init__(self, owner_id: int, *, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.owner_id = owner_id
        self.message = None

    async def on_timeout(self):
        """Disable all buttons after timeout"""
        for item in self.children:
            item.disabled = True
        if self.message:  # only edit if message is set
            await self.message.edit(view=self)

    @dc.ui.button(label="Rotieren", style=dc.ButtonStyle.secondary, emoji="🔄")
    async def rotate_callback(self, interaction: dc.Interaction, button):
        """Assign the player to team rotate and give them a rotation degree amount"""
        user_id = interaction.user.id
        global last_rot

        if user_id in rotation_player_group:
            await interaction.response.send_message(f"Du bist schon im Team `{translations[rotation_player_group[user_id]]}`", ephemeral=True)
            return

        rotation_player_group[user_id] = "rot"
        if last_rot == 8:
            rotation_player_value[user_id] = 3
            last_rot = 3
        else:
            rotation_player_value[user_id] = 8
            last_rot = 8
            
        rview = RotateView(user_id)
        await interaction.response.send_message(f"<@{user_id}> wurde Team `{translations[rotation_player_group[user_id]]}` zugeteilt und kann `{rotation_player_value[user_id]*10}` Grad drehen")
        button_msg = await interaction.followup.send(f"Hier kannst du weitermachen <@{user_id}>", view=rview)
        rview.message = button_msg

    @dc.ui.button(label="Zoomen", style=dc.ButtonStyle.secondary, emoji="🔍")
    async def zoom_callback(self, interaction: dc.Interaction, button):
        """Assign the player to team zoom and give them a zoom amount"""
        user_id = interaction.user.id
        global last_zoom

        if user_id in rotation_player_group:
            await interaction.response.send_message(f"Du bist schon im Team `{translations[rotation_player_group[user_id]]}`", ephemeral=True)
            return

        rotation_player_group[user_id] = "zom"
        if last_zoom == 8:
            rotation_player_value[user_id] = 3
            last_zoom = 3
        else:
            rotation_player_value[user_id] = 8
            last_zoom = 8
        zview = ZoomView(user_id)
        await interaction.response.send_message(f"<@{user_id}> wurde Team `{translations[rotation_player_group[user_id]]}` zugeteilt und kann `{rotation_player_value[user_id]}`-fach zoomen")
        button_msg = await interaction.followup.send(f"Hier kannst du weitermachen <@{user_id}>", view=zview)
        zview.message = button_msg

async def rotation_show(interaction: dc.Interaction):
    "Challenge to rotate and zoom an image to a target orientation"
    global rotation_state, target_state, rotation_player_group, rotation_player_value

    rotation_state = {"rot":0, "zom":0, "path":""}
    target_state = {"rot":0, "zom":0, "path":""}
    rotation_player_group = {}
    rotation_player_value = {}

    os.makedirs("TCG_images/challenge_images", exist_ok=True)

    con = sqlite3.connect("tcg.db")
    cur = con.cursor()

    cur.execute("SELECT image FROM tcgames")

    path_to_original_image = cur.fetchone()[0]

    con.close()

    file_path = f"TCG_images/challenge_images/rotation-{str(datetime.today().strftime('%Y-%m-%d'))}-{str(hash(time.time()))}.png"

    start_image = Image.open(path_to_original_image)
    target_image = Image.open(path_to_original_image)
    width, height = target_image.size

    rotation = random.randint(1,36)
    target_image = target_image.rotate(rotation*10)

    # zoom into the middle of the picture
    zoom = random.randint(2,10)
    new_width = width/zoom
    new_heigth = height/zoom
    left = (width - new_width)/2
    right = (width + new_width)/2
    top = (height - new_heigth)/2
    bottom = (height + new_heigth)/2
    target_image = target_image.crop((left, top, right, bottom))

    target_image.save(file_path, "PNG")

    target_state["rot"] = rotation
    target_state["zom"] = zoom
    target_state["path"] = file_path
    rotation_state["path"] = path_to_original_image

    print(target_state)
    print(rotation_state)

    cview = ChallengeView(interaction.user.id)
    button_msg = await interaction.followup.send(
        "Rotiert und zoomt das Bild bis es gleich aussieht wie das schon rotierte und gezoomte Bild!",
        files=[
            dc.File(path_to_original_image, filename="start.png"),
            dc.File(file_path, filename="target.png")
        ],
        view=cview
    )
    cview.message = button_msg

async def check(interaction: dc.Interaction):
    user_id = interaction.user.id

    await interaction.response.defer()

    con = sqlite3.connect("tcg.db")
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tcgames (
        start_time_unix INTEGER,
        playing INTEGER,
        type INTEGER,
        image TEXT
    )
    """)

    # make sure one row exists
    cur.execute("""
    INSERT INTO tcgames (start_time_unix, playing, type, image)
    SELECT 0, 0, 0, ''
    WHERE NOT EXISTS (SELECT 1 FROM tcgames)
    """)

    # now safe to fetch
    cur.execute("SELECT playing, start_time_unix FROM tcgames")
    row = cur.fetchone()
    playing, start_time = row

    con.commit()
    con.close()

    if not playing:
        await interaction.followup.send("Es läuft gerade keine Challenge", ephemeral=True)
        return

    print(target_state)
    print(rotation_state)

    target_image = Image.open(target_state["path"])
    current_image = Image.open(rotation_state["path"])
    width, height = current_image.size
    current_image = current_image.rotate(rotation_state["rot"]*10)

    zoom = rotation_state["zom"]
    if zoom != 0:
        new_width = width/zoom
        new_heigth = height/zoom
        left = (width - new_width)/2
        right = (width + new_width)/2
        top = (height - new_heigth)/2
        bottom = (height + new_heigth)/2
        current_image = current_image.crop((left, top, right, bottom))

    buffer = io.BytesIO()
    current_image.save(buffer, format="PNG")   # or "JPEG"
    buffer.seek(0)

    await interaction.followup.send(
        "Das ist der momentane Stand:",
        files=[
            dc.File(buffer, filename="start.png"),
            dc.File(target_state["path"], filename="target.png")
        ]
    )

    if (rotation_state["rot"] % 36 == target_state["rot"] or rotation_state["rot"] % 36 == -target_state["rot"]) and rotation_state["zom"] == target_state["zom"]:
        await interaction.followup.send("IHR HABTS GESCHAFFT. IHR ALLE BEKOMMT EIN TOKEN!")
        con = sqlite3.connect("tcg.db")
        cur = con.cursor()
        cur.execute("""
            UPDATE user_tokens
            SET tokens = tokens + 1;
        """)
        cur.execute("""
            UPDATE tcgames
            SET playing = ?, image = ?
        """, (0, ""))
        con.commit()
        con.close()
        return

    cview = ChallengeView(user_id)
    button_msg = await interaction.followup.send("Neue Spieler können sich hier einem Team anschließen", view=cview)
    cview.message = button_msg

    if user_id in rotation_player_group:
        if rotation_player_group[user_id] == "rot":
            rview = RotateView(user_id)
            button_msg = await interaction.channel.send(f"Hier kannst du weitermachen <@{user_id}>", view=rview)
            rview.message = button_msg
        elif rotation_player_group[user_id] == "zom":
            zview = ZoomView(user_id)
            button_msg = await interaction.channel.send(f"Hier kannst du weitermachen <@{user_id}>", view=zview)
            zview.message = button_msg
