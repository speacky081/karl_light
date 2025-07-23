import discord as dc
from discord.ext import commands
from ugame.ugame_functions import UgfBoard
from ugame.ugame_functions import UgfPlayer
from discord.ext.commands import Context as Ctx
import os
from discord.ui import Button, View
from typing import Dict
from ugame.utils import fill_strings_to_same_length
import shutil
import random as rand
from discord.ext import tasks
import time
import json
from datetime import datetime

path_karl_ugame = "ugame"

class UgameCommands(commands.Cog):
    '''
    Cog for ugame
    '''
    def __init__(self, bot):
        self.bot = bot
        self.boards:Dict[str,UgfBoard] = {}
        self.load_all()
        self.running_dict = {board:0 for board in self.boards.values()}
        self.messages_to_refresh = {}       #not used!
        #self.refresh_messages.start()
        self.last_message = {}
        if os.path.exists(f"{path_karl_ugame}/savedata_savedata_last_activity.json"):
            with open(f"{path_karl_ugame}/savedata_last_activity.json", "r", encoding="utf-8") as last_activity:
                self.last_message = json.load(last_activity)

    class CustomButton(Button):
        '''
        Discord Button with custom properties
        '''
        def __init__(self, label, user_id, cb, space=None, item=None, target=None, style=dc.ButtonStyle.secondary):
            super().__init__(label=label, style=style)
            self.user_id = user_id
            self.cb = cb
            self.space = space
            self.item = item
            self.target = target

        async def callback(self, interaction: dc.Interaction):
            if interaction.user.id == self.user_id:
                # Perform actions for the intended user
                await self.cb(self, interaction)
            else:
                # Respond to unauthorized users
                await interaction.response.send_message("Du darfst diesen Knopf nicht drücken!", ephemeral=True)

    def load_all(self):
        '''load all data'''
        for item in os.listdir(f"{path_karl_ugame}"):
            if item.startswith("savedata_") and os.path.isdir(f"{path_karl_ugame}/{item}"):
                id = item[9:]
                self.boards[id] = UgfBoard(1, id, id, 0, False)
                self.boards[id].load()

    @commands.Cog.listener()
    async def on_message(self, message:dc.Message):
        if message.author.id == self.bot.user.id:
            self.last_message[str(message.channel.id)] = time.time()
            with open(f"{path_karl_ugame}/savedata_last_activity.json", "w", encoding="utf-8") as save_activiy:
                json.dump(self.last_message, save_activiy, indent=4)

    @commands.group("ugame", aliases = ["u"], help = "Unbekanntes Spiel. Kurz 'u'")
    async def ugame(self, ctx:Ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("invalider command")

    @ugame.command("initialize", aliases = ["i"], help = "Initialisiert ein neues Spiel. Optional: Größe (default=8), Abstand Flamingo zu Feld 0 (default=5)")
    async def ugame_initialize(self, ctx:Ctx, size=8, flamingo_distance=5):
        if str(ctx.channel.id) in self.boards:
            await ctx.send("Es existiert bereits ein Spiel in diesem Channel!")
            return
        thread = await ctx.message.create_thread(name=f"{ctx.author.name}s Spiel")
        new_board = UgfBoard(size, thread.id, thread.id, flamingo_distance, True)
        self.boards[str(thread.id)] = new_board
        self.running_dict[new_board] = False
        self.boards[str(thread.id)].save()


    @ugame.command("join", aliases = ["j"], help="Tritt einem Spiel bei")
    async def ugame_join(self, ctx:Ctx):
        last_activity = datetime.fromtimestamp(self.last_message[str(ctx.channel.id)]-10800)
        current_time_normal = datetime.fromtimestamp(time.time()-10800)
        if not self.running_dict[self.boards[str(ctx.channel.id)]] or last_activity.year != current_time_normal.year or last_activity.month != current_time_normal.month or last_activity.day != current_time_normal.day:
            is_already = False
            for player in self.boards[str(ctx.channel.id)].players:
                if player.id == ctx.author.id:
                    is_already = True
                    break

            if not is_already:
                current_turn_rank = -1
                for player in self.boards[str(ctx.channel.id)].players:
                    if player.turn_rank >= current_turn_rank:
                        current_turn_rank = player.turn_rank
                Player = UgfPlayer(ctx.author.name, ctx.author.id, current_turn_rank+1, self.boards[str(ctx.channel.id)])
                self.boards[str(ctx.channel.id)].add_player(Player)
                Player.save()
                self.boards[str(ctx.channel.id)].save()
                await ctx.send(f"{ctx.author.name} ist dem Spiel beigetreten!")
            else:
                await ctx.reply(f"Du bist schon in diesem Spiel!", ephemeral=True)
        else: 
            await ctx.send("Das Spiel läuft schon. Du bist zu spät du Lappen!", ephemeral=True)


    @ugame.command("start", aliases = ["s"], help="Startet das Spiel wenn alle bereit sind")
    async def ugame_start(self, ctx:Ctx):
        if not self.running_dict[self.boards[str(ctx.channel.id)]] or ((time.time() - self.last_message[str(ctx.channel.id)])>900):
            if isinstance(ctx.channel, dc.threads.Thread):
                current_players = [p.id for p in self.boards[str(ctx.channel.id)].players]
                if ctx.author.id in current_players:
                    await self.player_turn(ctx, rank=int(self.boards[str(ctx.channel.id)].current_turn))
                    self.running_dict[self.boards[str(ctx.channel.id)]] = True
                else:
                    await ctx.reply("Du bist nichtmal im Spiel du Affe", ephemeral=True)
        else:
            await ctx.send("Fick dich du Hurensohn!", ephemeral=True)

    async def player_turn(self, ctx:Ctx, rank, moved=False):
        
        current_board = self.boards[str(ctx.channel.id)]
        if rank >= len(current_board.players):
            rank = 0

        current_player = None
        for player in self.boards[str(ctx.channel.id)].players:
            if player.turn_rank == rank:
                current_player = player
                break
        moved = current_player.moved

        view = View()
        


        async def move_cb(button: UgameCommands.CustomButton, interaction: dc.Interaction):
            #make a new view to house the directional buttons
            move_view = View()

            #disable all buttons
            for b in view.children:
                b.disabled = True
            await interaction.response.edit_message(view=view)
            

            #get direcetions for the buttons later
            directions = current_board.directions(current_player)
            

            #handle the move-action
            async def direction_cb(button: UgameCommands.CustomButton, interaction: dc.Interaction):
                await interaction.response.defer()

                button.style = dc.ButtonStyle.success

                # Disable all movement buttons
                for item in move_view.children:
                    if isinstance(item, UgameCommands.CustomButton):
                        item.disabled = True
                # Update the message with the new view state
                await interaction.message.edit(view=move_view)

                # Process the move
                if "stumble" in current_player.effects:
                    directions_list = [d for d in directions]
                    button.space = str(rand.choice(directions_list))
                    current_player.effects.remove("stumble")
                    await ctx.send("Du fliegst böse aufs Gesicht und landest irgendwo anders... :(")
                move_return = current_board.move(current_player, str(button.space))
                for p in current_board.players:
                    if p!= current_player and p.position == current_player.position:
                        await ctx.send(f"Du erkennst ein Gesicht am Horizont. Es ist <@{p.id}>!")
                current_player.moved = True
                if "range" in current_player.effects:
                    current_player.effects.remove("range")

                translations = {"bad":"Schlecht", "good":"Gut","empty":"Leer","flamingo":"Flamingo","shop":"Laden","trap":"Du trittst in eine Falle! Das scheint ganz schön wehzutun","money":"Du findest ein kleines Säckchen mit Geld!"}

                if not move_return[0]:
                    await interaction.followup.send("Das hat nicht funktioniert. Komisch...")
                    
                elif move_return[2]:
                    current_player.moved = True
                    further_effects_string = ""
                    for effect in move_return[2]:
                        further_effects_string += f", {translations[effect]}"
                    await ctx.send(f"Du landest auf folgendem Feld: {translations[move_return[1]]}\nDir passiert außerdem folgendes: {further_effects_string}")
                    
                else:
                    current_player.moved = True
                    await ctx.send(f"Du landest auf folgendem Feld: {translations[move_return[1]]}")
                    
                
                current_player.save()

                if move_return[1] in ["empty","good", "bad", "shop", "flamingo"]:
                    match move_return[1]:
                        
                        case "empty":
                            await self.player_turn(ctx, rank, current_player.moved)

                        case "good":
                            good_returns = current_player.good(current_board)
                            good_translations = {"money":"Geldspritze",
                                                 "range":"Du kannst beim nächsten Mal doppelt so weit laufen",
                                                 "again":"Du kannst nochmal laufen",
                                                 "steal_money":"Du stiehlst jemandem Geld",
                                                 "steal_item":"Du stiehlst jemandem ein Item"}
                            message = await ctx.send(f"Du drehst am Glücksrad: {good_translations[good_returns[0]]}")
                            if len(str(good_returns[1]))>0:
                                extra_info_str = f"Du erhälst {good_returns[1]}"
                                await message.edit(content=message.content + " " + extra_info_str)
                            if "again" in current_player.effects:
                                current_player.moved = False
                                current_player.effects.remove("again")
                                print("This is a debug print to see if the 'again' effect has been affected. This print is in line 180 in unknow_game_game.py")
                            await self.player_turn(ctx, rank, current_player.moved)
                        case "bad":
                            bad_returns = current_player.bad(current_board)
                            bad_translations = {"stumble":"Stolpern",
                                                "loose_money":"Strafe zahlen",
                                                "teleport":"Teleportation. Du wirst irgendwo hinteleportiert",
                                                "swap":"Frauentausch. Du und ein zufälliger Spieler tauschen Plätze",
                                                "rearrange":"Spielfeldänderung. Der Typ eines Feldes hat sich geändert"}
                            message = await ctx.send(f"Du drehst am Pechsrad: {bad_translations[bad_returns[0]]}")
                            if len(str(bad_returns[1]))>0:
                                extra_info_str = ""
                                match bad_returns[1]:
                                    case "loose_money":
                                        extra_info_str = "Du verlierst " + str(bad_returns[1])
                                    case "swap":
                                        extra_info_str = f"Du und <@{bad_returns[1]} tauschen Plätze"
                                        for p in current_board.players:
                                            p.save()
                                    case "rearrange":
                                        extra_info_str = f"Es gibt jetzt ein {translations[bad_returns[1]]} mehr"

                                await message.edit(content=message.content + extra_info_str)
                            await self.player_turn(ctx, rank, current_player.moved)
                        case "shop":
                            async def return_cb(button:UgameCommands.CustomButton, interaction:dc.Interaction):
                                for b in button.view.children:
                                    b.disabled = True
                                await interaction.message.edit(view=button.view)
                                await interaction.response.defer()
                                await self.player_turn(ctx, rank)
                            shop_start_view = View()
                            shop_start_view.add_item(UgameCommands.CustomButton(label="Shoppen", user_id=current_player.id, cb=shop_cb, style=dc.ButtonStyle.primary))
                            shop_start_view.add_item(UgameCommands.CustomButton(label="Zurück", user_id=current_player.id, cb=return_cb, style=dc.ButtonStyle.danger))
                            message_shop_start_view = await ctx.send("Hier drücken wenn du shoppen willst:",view=shop_start_view)
                            self.messages_to_refresh[message_shop_start_view.id] = (shop_start_view, ctx.channel.id)

                        case "flamingo":
                            await ctx.send(f"<@{current_player.id}> hat das Flamingo-Feld gefunden. Das Spiel ist vorbei!")
                            with open(f"{path_karl_ugame}/savedata_{current_board.name}/saveboard.jpg", "rb") as board_image:
                                await ctx.send(file=dc.File(board_image, "Spielfeld.jpg", description="Das Spielfeld. Mal schauen ob das so aussieht wie du dir das vorgestellt hast..."))
                            for p in current_board.players:
                                await ctx.send(f"{p.name}s Position: {p.position}")
                                self.running_dict.pop(current_board)
                            shutil.rmtree(f"{path_karl_ugame}/savedata_{current_board.name}")
                            return
                            

                current_player.save()

            # Add buttons for each direction
            for space in directions:        
                direction = directions[space]["direction"]
                move_view.add_item(UgameCommands.CustomButton(label=direction, user_id=current_player.id, cb=direction_cb, space = space))

            # Send the view with direction buttons
            message_directions = await interaction.followup.send("Wähle eine Richtung:", view=move_view)
            self.messages_to_refresh[message_directions.id] = (move_view, ctx.channel.id)




        async def shop_cb(button:UgameCommands.CustomButton, interaction:dc.Interaction):
            
            shop_view = View()
            
            for b in button.view.children:
                b.disabled = True
            await interaction.response.edit_message(view=button.view)


            async def buy_cb(button: UgameCommands.CustomButton, interaction: dc.Interaction):
                await interaction.response.defer()
                for b in button.view.children:
                    b.disabled=True
                await interaction.message.edit(view=shop_view)
                
                item = button.item

                buy_returns = current_board.buy(current_player, item)
                if buy_returns[0] and buy_returns[1] and buy_returns[2] and not buy_returns[3]:
                    await interaction.followup.send(f"Erfolgreich {item} gekauft")
                elif not buy_returns[1]:
                    await interaction.followup.send(f"Du hast nicht genug Geld")
                elif not buy_returns[2]:
                    await interaction.followup.send(f"Der Gegenstand ist ausverkauft")
                elif buy_returns[3]:
                    await interaction.followup.send(f"Invalider Gegenstand")
                current_player.save()
                await self.player_turn(ctx, rank, current_player.moved)

            #make the shop string
            items = []
            prices = []
            amounts = []
            descriptions = []

            for item in current_board.shop:
                items.append(item)
                prices.append(str(current_board.shop[item]["price"]))
                amounts.append(str(current_board.shop[item]["amount_left"]))
                descriptions.append(current_board.shop[item]["description"])
                shop_view.add_item(UgameCommands.CustomButton(label = str(item), user_id=current_player.id, cb = buy_cb, item=item))

            items_aligned = fill_strings_to_same_length(items)
            prices_aligned = fill_strings_to_same_length(prices)
            amounts_aligned = fill_strings_to_same_length(amounts)
            descriptions_aligned = fill_strings_to_same_length(descriptions)
            
            shop_str = ""
            
            for i in range(len(current_board.shop)):
                shop_str += f"{items_aligned[i]}: Preis: {prices_aligned[i]}, Anzahl: {amounts_aligned[i]}, Beschreibung: {descriptions_aligned[i]}\n\n"

            shop_str = f"Dein Kontostand: {current_player.money}\n" + shop_str
            current_board.save()
            current_player.save()

            message_shop = await interaction.followup.send(f"```{shop_str}```", view=shop_view)
            self.messages_to_refresh[message_shop.id] = (shop_view, ctx.channel.id)
            


        async def end_cb(button:UgameCommands.CustomButton, interaction:dc.Interaction):
            for b in view.children:
                b.disabled = True
            await interaction.response.edit_message(view=view)
            current_player.moved = False
            current_player.used_item = False
            current_player.save()
            current_board.save()
            await ctx.send("Der nächste ist dran!")
            await self.player_turn(ctx, rank+1)
        


        async def item_cb(button:UgameCommands.CustomButton, interaction:dc.Interaction):
            await interaction.response.defer()
            item_view = View()
            for b in button.view.children:
                b.disabled = True
            await interaction.message.edit(view=button.view)


            async def use_item_cb(button:UgameCommands.CustomButton, interaction:dc.Interaction):
                
                for b in button.view.children:
                    b.disabled = True
                await interaction.response.edit_message(view=button.view)

                if button.item in ["swap", "staff", "dagger"]:
                    async def use_item_on_target_cb(button2:UgameCommands.CustomButton, interaction:dc.Interaction):
                        await interaction.response.defer()
                        for b in button.view.children:
                            b.disabled = True
                        await interaction.message.edit(view=button.view)
                        item_return = current_player.use_item(button.item, button2.target)
                        current_player.used_item = True
                        if item_return[0]:
                            await ctx.send(f"Du benutzt {button.item} auf  {button2.target.name}")
                            match button.item:
                                case "swap":
                                    await ctx.send(f"Ihr habt eure Positionen getauscht. Ich hoffe ihr habt gut mitgeschrieben")
                                case "staff":
                                    bad_return = button2.target.bad()
                                    if bad_return[1]:
                                        await ctx.send(f"{button2.target} dreht am Glücksrad {bad_return[0]} und verliert {bad_return[1]}")
                                    else:
                                        await ctx.send(f"{button2.target} dreht am Glücksrad {bad_return[0]}")
                                case "dagger":
                                    await ctx.send(f"Du stichst brutal zu und erhälst {item_return[1]}")
                            current_player.save()
                            for p in current_board.players:
                                p.save()
                        await self.player_turn(ctx, rank)
                    message_view = View()
                    if button.item != "dagger":
                        for player in current_board.players:
                            if player != current_player:
                                message_view.add_item(UgameCommands.CustomButton(label=player.name, user_id=current_player.id, cb=use_item_on_target_cb, target=player))
                                message_use_item_on_player = await ctx.send("Auf wen willst du das anwenden?", view=message_view)
                                self.messages_to_refresh[message_use_item_on_player.id] = (message_view, ctx.channel.id)
                    else:
                        for player in current_board.players:
                            if player != current_player and player.position == current_player.position:
                                message_view.add_item(UgameCommands.CustomButton(label=player.name, user_id=current_player.id, cb=use_item_on_target_cb, target=player))
                    message_use_item_on_player2 = await ctx.send("Auf wen willst du das anwenden?", view=message_view)
                    self.messages_to_refresh[message_use_item_on_player2.id] = (message_view, ctx.channel.id)
                    return

                else:
                    item_return = current_player.use_item(button.item, UgfPlayer(None, None, None, current_board))
                    current_player.used_item = True
                    if item_return[0]:
                        await ctx.send(f"Erfolgreich {button.item} benutzt!")
                        match button.item:
                            case "compass":
                                await ctx.send(f"Der Kompass verrät dir ein kleines Geheimnis.\nUm dich herum befinden sich folgende Felder: {item_return[1]}")
                            case "trap":
                                await ctx.send(f"Hier befindet sich jetzt eine Falle. Vergiss das ja nicht 👀")
                    else:
                        await ctx.send("Das hat nicht funktioniert. Komisch...")
                await self.player_turn(ctx, rank)


            inventory_dict = {}

            for item in current_player.inventory:
                if item in inventory_dict:
                    inventory_dict[item] += 1
                else:
                    inventory_dict[item] = 1

            inventory_items = [x for x in inventory_dict]
            inventory_items_aligned = fill_strings_to_same_length(inventory_items)

            inv_str = ""

            for i in range(len(inventory_items_aligned)):
                inv_str += f"{inventory_items_aligned[i]} : Anzahl = {inventory_dict[inventory_items[i]]}\n\n"

            for item in inventory_dict:
                item_button = UgameCommands.CustomButton(label=item, user_id=current_player.id,cb=use_item_cb, item=item)
                item_view.add_item(item_button)
                if item == "dagger":
                    on_space = []
                    for player in current_board.players:
                        if player.position == current_player.position and player != current_player:
                            on_space.append(player)
                    if len(on_space)<1:
                        item_button.disabled = True
                if item == "staff":
                    if len(current_board.players)<2:
                        item_button.disabled = True
                if item == "swap":
                    if len(current_board.players)<2:
                        item_button.disabled = True

            message_inventory = await interaction.followup.send(f"```{inv_str}```", view=item_view)
            self.messages_to_refresh[message_inventory.id] = (item_view, ctx.channel.id)



        async def info_cb(button:UgameCommands.CustomButton, interaction:dc.Interaction):
            for b in button.view.children:
                b.disabled = True
            await interaction.message.edit(view=button.view)
            await interaction.response.defer()
            embed = dc.Embed(title=f"{current_player.name} ({current_player.turn_rank})", color=dc.Color.greyple())

            # Inventory
            inv_str = ""
            if len(current_player.inventory)>0:
                inv_dict = {}
                for item in current_player.inventory:
                    if item in inv_dict:
                        inv_dict[item] += 1
                    else:
                        inv_dict[item] = 1
                
                items_list = []
                for item in inv_dict:
                    items_list.append(item)
                
                amount_list = []
                for amount in inv_dict:
                    amount_list.append(str(inv_dict[amount]))

                items_list_aligned = fill_strings_to_same_length(items_list)
                amount_list_aligned = fill_strings_to_same_length(amount_list)

                for i in range(len(items_list_aligned)):
                    inv_str += f"{items_list_aligned[i]} : {amount_list_aligned[i]}\n"
            else:
                inv_str = "Leer :("

            embed.add_field(name="Inventar",
                            value=f"```\n{inv_str}\n```",
                            inline=True)
            
            # Money
            info_str = f"Geld: {current_player.money}"

            embed.add_field(name="Geld",
                            value=f"```\n{info_str}\n```",
                            inline=True)
            
            # Effects
            effects_str = ""
            if len(current_player.effects)>0:
                for effect in current_player.effects:
                    effects_str += f"{effect}\n"
            else:
                effects_str = "Leer :("
            embed.add_field(name=f"Effekte",
                            value=f"```\n{effects_str}\n```",
                            inline=False)

            embed.set_thumbnail(url=interaction.user.display_avatar.url)

            await ctx.send(embed=embed)
            await self.player_turn(ctx, rank)


        info_button = UgameCommands.CustomButton(label="Info", user_id=current_player.id, cb = info_cb, style=dc.ButtonStyle.secondary)
        view.add_item(info_button)

        move_button = UgameCommands.CustomButton(label="Bewegen", user_id=current_player.id, cb = move_cb, style=dc.ButtonStyle.secondary)
        move_button.disabled = moved
        view.add_item(move_button)

        item_button = UgameCommands.CustomButton(label="Item benutzen", user_id=current_player.id, cb=item_cb, style=dc.ButtonStyle.secondary)
        if len(current_player.inventory)<1 or current_player.used_item:
            item_button.disabled = True
        view.add_item(item_button)

        view.add_item(UgameCommands.CustomButton(label="Zug beenden", user_id=current_player.id, cb = end_cb, style=dc.ButtonStyle.danger))
        main_message = await ctx.send(f"Was möchtest du tun <@{current_player.id}>?", view=view)
        self.messages_to_refresh[main_message.id] = (view, ctx.channel.id)
