import random as rand
import os
import math
from typing import List
from random import randint
import json
import networkx as nx
import matplotlib.pyplot as plt

path_karl_ugame = "ugame"

class UgfPlayer():
    '''
    When creating a player, give:
    the name,
    the user_id,
    their turn when they are supposed to play,
    their effects,
    their position,
    their inventory
    their money

    Defaults: effects = []; position = "0"; inventory = []; money = 5
    '''
    def __init__(
        self,
        name,
        ident,
        turn_rank,
        board: "UgfBoard",
        effects = [],
        position = "0",
        inventory = [],
        money = 5,
        moved=False,
        used_item=False
        ):
        self.name = name
        self.id = ident
        self.turn_rank = turn_rank
        self.effects = effects
        self.position = position
        self.inventory = inventory
        self.money = money
        self.board = board
        self.moved = moved
        self.used_item = used_item

    def add_effect(self, effect):
        '''add an effect out of the following list: stumble, range, again'''
        if effect in ["stumble", "range", "again"]:
            self.effects.append(effect.lower())
        else:
            raise ValueError(f"Invalid effect: {effect} is not an effect")

    def remove_effect(self, effect):
        '''remove an effect from the player'''
        if effect in self.effects:
            self.effects.remove(effect.lower())
        else:
            raise ValueError(f"Invalid effect: {effect} is not an effect")

    def good(self, board):
        '''make a player spin the 'good wheel' 

        Effects: money, range, again, steal money, steal item
        Returns the effect and the item/money/player'''
        effects = ["money", "money", "range", "again", "steal_money", "steal_money", "steal_item"]
        effect = rand.choice(effects)
        return_item = ""
        match effect:
            case "money":
                amount = randint(1,5)
                self.money += amount
            case "range":
                self.add_effect("range")
            case "again":
                self.add_effect("again")
            case "steal_money":
                is_self = True              #check that the victim is not the player themself
                victim = self
                while is_self and len(board.players) > 1:
                    victim = rand.choice(board.players)
                    if victim != self:
                        is_self = False
                amount_stolen = randint(1,5)
                victim.money -= amount_stolen
                self.money += amount_stolen
                return_item = str(amount_stolen)
            case "steal_item":
                is_self = True              #check that the victim is not the player themself
                victim = self
                while is_self and len(board.players) > 1:
                    victim = rand.choice(board.players)
                    if victim != self:
                        is_self = False
                if len(victim.inventory):       #see if victim inv is not empty
                    stolen_item = rand.choice(victim.inventory)
                    self.inventory.append(stolen_item)
                    victim.inventory.remove(stolen_item)
                    return_item = stolen_item
        return effect, return_item

    def bad(self, board):
        '''make a player spin the 'bad wheel' 
        
        Effects: stumble, loose money, teleport, swap, rearrange
        Returns the effect and the item/money/player'''
        effects = ["stumble", "loose_money", "teleport", "swap", "rearrange"]
        effect = rand.choice(effects)
        return_item = ""

        match effect:
            case "stumble":
                self.effects.append("stumble")
            case "loose_money":
                amount = randint(1,5)
                self.money -= amount
                return_item = amount
            #new_space is a string
            case "teleport":
                new_space = rand.choice(list(board.spaces.keys()))
                self.position = new_space
                return_item = new_space
            #board.players contains UgfPlayer class
            case "swap":
                while True:
                    victim = rand.choice(board.players)
                    if victim != self or len(board.players)<2:
                        break
                victim_space = victim.position
                victim.position = self.position
                self.position = victim_space
                return_item = victim.id
            case "rearrange":
                new_effects = ["shop", "empty", "empty", "empty", "good", "bad"]
                is_flamingo = True
                while is_flamingo:
                    changed_space = rand.choice(list(board.spaces.keys()))
                    if self.board.spaces[changed_space]["type"] != "flamingo":
                        is_flamingo = False
                new_type = rand.choice(new_effects)
                board.spaces[changed_space]["type"] = new_type
                return_item = new_type  
        return effect, return_item

    def save(self):
        '''Save the player as json'''
        player = {
            "name": self.name,
            "id": self.id,
            "turn_rank": self.turn_rank,
            "effects": self.effects,
            "position": self.position,
            "inventory": self.inventory,
            "money": self.money,
            "board": self.board.name,
            "moved": self.moved,
            "used_item": self.used_item
            }
        # Define the path where you want to create the file
        folder_path = f"{path_karl_ugame}/savedata_{self.board.name}/saveplayers"
        file_name = f"{self.id}.json"
        file_path = os.path.join(folder_path, file_name)

        # Check if the folder exists, if not, create it
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Write data to the JSON file
        with open(file_path, 'w', encoding="utf-8") as json_file:
            json.dump(player, json_file, indent=4)

    def use_item(self, item, target: 'UgfPlayer'):
        '''
        Let a player use an item.
        Returns the effect that happened and if the action was a success.\n
        **Caution**: If staff is used, effect is a tuple with the effect at 0 and the player/money/item at 1\n
        Deletes the item from the players inventory
        '''
        success = False
        returns = ""
        if item in self.inventory:
            match item:
                case "swap":       #swap two players
                    victim = rand.choice(self.board.players)
                    victim_pos = victim.position
                    victim.position = self.position
                    self.position = victim_pos
                    success = True
                case "compass":     #get the types of all adjacent spaces
                    adjacent_spaces = self.board.get_connections(self.position)
                    types = []
                    for space in adjacent_spaces:
                        types.append(self.board.spaces[space]["type"])
                    returns = types
                    success = True
                case "staff":       #make another player spin the bad wheel
                    effect = target.bad(target.board)
                    returns = effect
                    success = True
                case "dagger":      #steals 1-4 money from another player on the same space
                    if self.position == target.position:
                        amount_stolen = randint(1,4)
                        self.money += amount_stolen
                        target.money -= amount_stolen
                        returns = amount_stolen
                        success = True
                case "trap":        #lays a trap on the current space
                    self.board.spaces[self.position]["attributes"].append("trap")
                    success = True
                case "gold_potion":     #lets a small amount of money spawn on an adjacent space
                    money_space = rand.choice(self.board.get_connections(self.position))
                    # amount = randint(1,4)
                    # tuple = {"money": amount}
                    self.board.spaces[money_space]["attributes"].append("money")
                    # returns = amount
                    success = True
            self.inventory.remove(item)
        return success, returns


class UgfBoard():
    '''
    When creating an instance of board, give:
    the desired size (best between 6-8)
    the name under which the board is to be saved
    the channel id
    '''
    def __init__(
        self,
        size,
        name,
        channel_id,
        flamingo_distance = 5,
        initialize=True,
        current_turn=0
        ):
        self.size = size
        self.name = name
        self.players:List[UgfPlayer] = []
        self.channel = channel_id
        self.current_turn = current_turn
        self.shop = {
            "swap": {
                "price":4,
                "amount_left":2,
                "description":"Wechselt die Position von dir und einem Spieler deiner Wahl"},
            "compass": {
                "price":3,
                "amount_left":5,
                "description":"sagt dir, was sich auf allen anliegenden Feldern befindet"},
            "staff": {
                "price":3,
                "amount_left":3,
                "description":"gib einem Spieler einen zufälligen schlechten Effekt"},
            "dagger":{
                "price":2,
                "amount_left":3,
                "description":"stiehl einem Spieler 2 Gold"},
            "trap": {
                "price":2,
                "amount_left":3,
                "description":"stelle eine Falle die einem Spieler 2 Gold stieht"},
            "gold_potion": {
                "price":1,
                "amount_left":4,
                "description":"lässt auf einem anliegenden Feld ein bisschen Gold erscheinen"}
            }

        if initialize:
            valid_board = False     #board is valid if there exists a flamingo space, all spaces are connected to all other spaces and the distance between flamingo and o is at least "flamingo_distance"
            while not valid_board:
                board = self.initialize()
                flamingo_space = None
                for space in board:
                    if board[space]["type"] == "flamingo":
                        flamingo_space = space
                        break
                valid_board = flamingo_space is not None and all(self.dfs(board, start=i) for i in board) and self.bfs(board)[flamingo_space] > flamingo_distance

    def move(self, player: UgfPlayer, target_space):
        '''
        move the player to a space.\n
        Returns True if success, the type of the space and the effects of the space (trap/money)
        '''
        success = False
        type = ""
        effects = []
        if "range" in player.effects:
            reachable_spaces = set()
            for space in self.get_connections(player.position):
                reachable_spaces.add(space)
                for subspace in self.get_connections(space):
                    reachable_spaces.add(subspace)
            if target_space in reachable_spaces:
                player.position = target_space
                success = True
        else:
            reachable_spaces = set()
            for space in self.get_connections(player.position):
                reachable_spaces.add(space)
            if target_space in reachable_spaces:
                player.position = target_space
                success = True

        #check the type and effects of the targetspace
        if success is True:
            type = self.get_type(target_space)
            for effect in self.get_attributes(target_space):
                effects.append(effect)
                match effect:
                    case "trap":
                        lost_money = randint(1,4)
                        player.money -= lost_money
                    case "money":
                        amount = randint(1,4)
                        player.money += amount
        return success, type, effects

    def initialize(self):
        '''Creates the spaces and the board'''
        temp_board = []
        #create a grid of (x,y) coordinates where about 3/5 of all possible spaces are created to later use as spaces
        for i in range(self.size):
            for j in range(self.size):
                if (i==0 and j==0) or randint(0,4) < 3:
                    temp_board.append((i,j))

        #make temp_board into a dict and index spaces, contains x and y coordinates
        self.spaces = {}
        for m in range(len(temp_board)):
            self.spaces[str(m)] = {"x": temp_board[m][0], "y": temp_board[m][1], "type": "", "connections": [], "attributes": []}
        space_keys = list(self.spaces.keys())

        #declare what types of spaces can exist
        effect_spaces = ["shop", "empty", "empty", "empty", "flamingo", "good", "bad"]
        flamingo_is_already = False

        #actually create the spaces
        for space_key in self.spaces:
            if space_key != "0":
                #set spacetype and make sure there is only ever one flamingo
                if flamingo_is_already:
                    effect_spaces_no_flamingo = ["shop", "empty", "empty", "empty", "good", "bad"]
                    space_type = rand.choice(effect_spaces_no_flamingo)
                    self.spaces[space_key]["type"] = space_type
                else:
                    space_type = rand.choice(effect_spaces)
                    if space_type == "flamingo":
                        flamingo_is_already = True
                    self.spaces[space_key]["type"] = space_type

                #Create 1-4 connections for every space
                connections = []
                num_connections = randint(1,3)
                for i in range(num_connections):
                    #make sure to make bi-directional connections and list the connections only once
                    connection = self.get_closest_space(space_key, self.spaces, connections)
                    #Check if space_key not already in connections of connection to avoid double listing it
                    if not space_key in self.spaces[connection]["connections"]:
                        self.spaces[connection]["connections"].append(str(space_key))
                    #Check if connection not already in connections of space_key to avoid double listing it
                    if not connection in connections:
                        connections.append(str(connection))
                self.spaces[space_key]["connections"] = connections

            else:
                self.spaces[space_key]["type"] = "empty"
                connections0 = []
                i = randint(2,4)
                k = 0
                #make sure 0 has at least 2 connections
                while k < i:
                    poss_connect = str(rand.choice(space_keys))
                    if poss_connect != "0":
                        k += 1
                        connections0.append(str(poss_connect))
                self.spaces["0"]["connections"] = connections0
        self.save()
        return self.spaces

    def dfs(self, board, visited = None, start = "0"):
        '''depth-first search'''
        if visited is None:
            visited = [False]*len(board)
        visited[int(start)] = True
        for connection in board[start]["connections"]:
            if not visited[int(connection)]:
                self.dfs(board, visited=visited, start=connection)
        return all(visited)

    def bfs(self, board, start = "0"):
        '''returns a dict with spaces and their distance to a given start space'''
        queue = [start]
        dist_dict = {i: None for i in board}
        dist_dict[start] = 0
        while len(queue):
            current = queue[0]
            queue.remove(current)
            for connection in board[current]["connections"]:
                if dist_dict[connection] is None:
                    dist_dict[connection] = dist_dict[current] + 1
                    queue.append(connection)
        return dist_dict

    def distance(self, space1, space2):
        '''Manhattan distance between two spaces'''
        # Manhattan distance between two spaces
        return abs(self.get_x(space1) - self.get_x(space2)) + abs(self.get_y(space1) - self.get_y(space2))

    def get_closest_space(self, space, board, current_connections):
        '''
        Get the closest space that is not already connected.
        Needs the current space, the entire board and all current connections as input
        '''
        unconnected_spaces = [s for s in board if s != space and s not in current_connections and s in self.spaces.keys()]
        if not unconnected_spaces:
            return None
        return min(unconnected_spaces, key=lambda s: self.distance(space, s))

    def get_x(self, space):
        '''Returns the x-coordinate of the space'''
        return self.spaces[space]["x"]

    def get_y(self, space):
        '''Returns the y-coordinate of the space'''
        return self.spaces[space]["y"]

    def get_attributes(self, space):
        '''Returns the attributes of the space'''
        return self.spaces[space]["attributes"]

    def get_type(self, space):
        '''Returns the type of the space (empty, good, bad, flamingo, shop)'''
        return self.spaces[space]["type"]

    def get_connections(self, space: str):
        '''
        Returns the connections of the space.
        Notably only gets the immediate connections; not the connections of connections.
        Space is expected to be a string
        '''
        return self.spaces[space]["connections"]

    def save(self):
        '''Save the current boardspaces to a json file under karl/ugame/savedata/savespaces.json'''
        # Define the path where you want to create the file
        folder_path = f"{path_karl_ugame}/savedata_{self.name}"
        file_name = "savespaces.json"
        shop_file_name = "saveshop.json"
        file_path = os.path.join(folder_path, file_name)
        shop_file_path = os.path.join(folder_path, shop_file_name)

        # Check if the folder exists, if not, create it
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        if not os.path.exists(f"{folder_path}/misc"):
            os.makedirs(f"{folder_path}/misc")

        # Write data to the JSON file
        with open(file_path, 'w', encoding='utf8') as json_file:
            json.dump(self.spaces, json_file, indent=4, ensure_ascii=False)

        with open(shop_file_path, 'w', encoding='utf8') as saveshop:
            json.dump(self.shop, saveshop, indent=4)

        with open(f"{folder_path}/misc/players.json", "w", encoding="utf-8") as misc_players:
            player_ids = {"ids":[]}
            for player in self.players:
                player_ids["ids"].append(player.id)
            json.dump(player_ids, misc_players)

        #Write channel id to a separate txt file
        with open(f"{folder_path}/misc/channel_id.txt", "w", encoding="utf-8") as channel_save:
            channel_save.write(str(self.channel))

        #write current turn to a separate txt file
        with open(f"{folder_path}/misc/current_turn.txt", "w", encoding="utf-8") as current_turn_save:
            current_turn_save.write(str(self.current_turn))

        self.visualize()

    def load(self):
        '''Load the current spaces'''
        with open(f"{path_karl_ugame}/savedata_{self.name}/savespaces.json", mode = "r", encoding="utf-8") as savespaces:
            self.spaces = json.load(savespaces)

        with open(f"{path_karl_ugame}/savedata_{self.name}/saveshop.json", mode = "r", encoding="utf-8") as saveshop:
            self.shop = json.load(saveshop)

        ids = []
        with open(f"{path_karl_ugame}/savedata_{self.name}/misc/players.json", "r", encoding="utf-8") as player_ids:
            ids_dict = json.load(player_ids)        #ids_dict looks like this: {"ids": []}
            for id in ids_dict["ids"]:
                ids.append(id)
        for id in ids:
            with open(f"{path_karl_ugame}/savedata_{self.name}/saveplayers/{id}.json", mode="r", encoding="utf-8") as saveplayer:
                player_dict = json.load(saveplayer)
                Player = UgfPlayer(player_dict["name"], player_dict["id"], player_dict["turn_rank"], self, player_dict["effects"], player_dict["position"], player_dict["inventory"], player_dict["money"], player_dict["moved"], player_dict["used_item"])
                self.add_player(Player)

        #get the channel id
        with open(f"{path_karl_ugame}/savedata_{self.name}/misc/channel_id.txt", "r", encoding="utf-8") as savechannel:
            self.channel = savechannel.read()

        #get the current turn
        with open(f"{path_karl_ugame}/savedata_{self.name}/misc/current_turn.txt", "r", encoding="utf-8") as current_turn_save:
            self.current_turn = current_turn_save.read()

    def print_board(self):
        '''Print the type of the board and the board itself'''
        print(type(self.spaces))
        print(self.spaces)

    def visualize(self):
        '''Create the image of the board'''
        #self.load()
        #Create a graph using networkx
        G = nx.DiGraph()

        #Add nodes and edges to the graph
        for space in self.spaces:
            data = self.spaces[space]
            G.add_node(space)
            for connection in data["connections"]:
                G.add_edge(space, connection)
        
        #create dictionary with spaces as keys and their type as values
        spaces_types = {}
        for space in G.nodes:
            spaces_types[space] = self.spaces[space]["type"]

        #add attributes to each node depending on thy type of the space
        nx.set_node_attributes(G, spaces_types, name="type")
        node_colors = {"empty":'gray',"shop":'yellow',"bad":'red',"good":'green',"flamingo":'pink'}
        #create an ordered list of colors in ascending order according to the order of the nodes
        colors = [node_colors[G.nodes[node]['type']] for node in G.nodes]
        #create a dictionary where the nodes are keys and their positions are values
        pos = {}
        for space in self.spaces:
            pos[space] = (self.get_x(space), self.get_y(space))
        edge_colors = 'black'

        try:
            nx.draw(G, pos, with_labels=True, node_color=colors, edge_color=edge_colors, font_color='white', font_size=8, arrows=True)
            plt.savefig(f"{path_karl_ugame}/savedata_{self.name}/saveboard.jpg")
            plt.clf()
        except ValueError as e:
            print("Error:", e)
            print("Problematic node:", [n for n in G.nodes() if not isinstance(n, tuple)])

    def add_player(self, player: UgfPlayer):
        '''Player needs to be type UgfPlayer'''
        self.players.append(player)
        #print(len(self.players))
        #print("_")

    def directions(self, player: UgfPlayer):
        '''Returns a dict with spaces as key and their angle to our space and the direction
        
        Divide the circle around the current position in 8 equal parts. Spaces are given appropriate directions based on which part of the circle they are on'''
        directions = ["oben", "rechts oben", "rechts", "rechts unten", "unten", "links unten", "links", "links oben"]
        if "range" in player.effects:
            connections_1 = self.get_connections(player.position)
            connections_2 = []      #2nd order connections
            for connection_1 in connections_1:
                connection_1_connections = self.get_connections(connection_1)
                for space in connection_1_connections:
                    connections_2.append(space)
            connections_2_proper = []
            [connections_2_proper.append(space_proper) for space_proper in connections_2 if space_proper not in connections_2_proper]
            connections_2_angle = {}
            for connection_2 in connections_2_proper:
                if connection_2 != player.position:
                    connections_2_angle[connection_2] = {}
                    connections_2_angle[connection_2]["angle"] = math.atan2(self.get_x(connection_2)- self.get_x(player.position),self.get_y(connection_2) - self.get_y(player.position))
                    #divide radian by 2pi then multiply by 8 then round. should give appr. location on the circle surrounding the space
                    connections_2_angle[connection_2]["direction"] = directions[(round(((connections_2_angle[connection_2]["angle"])/(2*math.pi))*8))%8]
            return connections_2_angle
        else:
            connections_1 = self.get_connections(player.position)
            connections_1_angle = {}
            for connection_1 in connections_1:
                connections_1_angle[connection_1] = {}
                connections_1_angle[connection_1]["angle"] = math.atan2(self.get_x(connection_1) - self.get_x(player.position),self.get_y(connection_1) - self.get_y(player.position))
                connections_1_angle[connection_1]["direction"] = directions[(round(((connections_1_angle[connection_1]["angle"])/(2*math.pi))*8))%8]
            return connections_1_angle

    def buy(self, player: UgfPlayer, item):
        '''Lets a player buy an item from the shop. Return a quadruplet of "bought, enough_money, in_stock, invalid_item"'''
        bought = False
        in_stock = False
        enough_money = False
        invalid_item = False
        item_price = self.shop[item]["price"]

        if item in self.shop:
            if item_price > player.money:
                pass
            elif int(self.shop[item]["amount_left"]) < 1:
                pass
            else:
                player.inventory.append(item)
                player.money -= item_price
                self.shop[item]["amount_left"] -= 1
                bought = True
                enough_money = True
                in_stock = True
        else:
            invalid_item = True
        return bought, enough_money, in_stock, invalid_item