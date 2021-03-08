import os
import datetime
import requests
import discord

import dateutil.parser

from discord import Embed
from discord.ext import tasks

from PIL import Image, ImageDraw, ImageFilter
from modules.ImageManipulator import ImageManipulator

class KillBot:

    ## Fixed URLs
    death_icon = "https://albiononline.com/assets/images/killboard/kill__date.png"
    kill_icon_win = "https://i.imgur.com/CeqX0CY.png"
    kill_icon_loss = "https://albiononline.com/assets/images/killboard/kill__date.png"
    item_images = "https://render.albiononline.com/v1/item/"
    ##

    def __init__ (self, cloud_name, cloud_key, cloud_secret, requiredAlliances=[], requiredGuilds=[], requiredPlayers=[]):
        self.requiredAlliances = requiredAlliances
        self.requiredGuilds = requiredGuilds
        self.requiredPlayers = requiredPlayers

        self.imageManipulator = ImageManipulator(cloud_name, cloud_key, cloud_secret)
        self.PostedKills = []   # to avoid double posting.
        self.KillImagesIDs = [] # to avoid taking too much space on cloudinary

    def EmbedKill(self, KillDataExport):
        """ Creates embed object(s) based on the relevent Kill Data """

        ## Setting default embed values. Would be overwritten later.
        embed_color = 0xF300FF
        kill_icon_url = self.kill_icon_win
        ##

        ## Design the main kill image
        kill_image = self.imageManipulator.GetBlankBackground()

        if not 'kEquipment' in KillDataExport:
            print (f'[ERR] {KillDataExport}')
            return
        kill_image = self.imageManipulator.InsertEquipment(kill_image, KillDataExport['kEquipment'], killer=True)
        kill_image = self.imageManipulator.InsertEquipment(kill_image, KillDataExport['vEquipment'], killer=False)

        KillerName, VictimName = KillDataExport['killer'], KillDataExport['victim']

        if len(KillDataExport['kAlliance']) > 1:
            KillerGuild = f"[{KillDataExport['kAlliance']}] {KillDataExport['kGuild']}"
        else:
            KillerGuild = f"        {KillDataExport['kGuild']}"
        
        if len(KillDataExport['vAlliance']):
            VictimGuild = f"[{KillDataExport['vAlliance']}] {KillDataExport['vGuild']}"
        else:
            VictimGuild = f"        {KillDataExport['vGuild']}"

        KillerIP = KillDataExport['kIP']
        VictimIP = KillDataExport['vIP']

        KillFame = KillDataExport['fame']

        kill_image = self.imageManipulator.InsertText(kill_image, KillerName, KillerGuild, KillerIP, killer=True)
        kill_image = self.imageManipulator.InsertText(kill_image, VictimName, VictimGuild, VictimIP, KillFame, KillDataExport['nAssists'], killer=False)

        kill_image_name = f"{KillDataExport['killer']}-{KillDataExport['victim']}"
        savedFile = self.imageManipulator.SaveImage(kill_image, kill_image_name, 'png')
        killImageURL, killImageID = self.imageManipulator.UploadImage(savedFile, kill_image_name)
        self.KillImagesIDs.append(killImageID)
        ##

        ## Design the inventory image, if any.
        VictimInventory = KillDataExport['vInventory']
        inventoryURL = None
        if len (VictimInventory) > 0:
            VictimInventoryImage = self.imageManipulator.CreateInventory(VictimInventory)
            inventoryName = f'{kill_image_name}-inventory'
            saveInventory = self.imageManipulator.SaveImage(VictimInventoryImage, inventoryName, 'png')
            inventoryURL, inventoryID = self.imageManipulator.UploadImage(saveInventory, inventoryName)
            self.KillImagesIDs.append(inventoryID)
        ##

        ## Overwrite embed defaults with Victory layout
        if KillDataExport['kAlliance'].strip() in self.requiredAlliances:
            embed_color = 0x00FF00
            kill_icon_url = self.kill_icon_win
        
        if KillDataExport['kGuild'].strip() in self.requiredGuilds:
            embed_color = 0x00FF00
            kill_icon_url = self.kill_icon_win

        ## Overwrite embed defaults with Loss layout
        if KillDataExport['vAlliance'].strip() in self.requiredAlliances:
            embed_color = 0xEC0000
            kill_icon_url = self.kill_icon_loss
        
        if KillDataExport['vGuild'].strip() in self.requiredGuilds:
            embed_color = 0xEC0000
            kill_icon_url = self.kill_icon_loss

        if VictimName.strip().lower() in self.requiredPlayers:
            embed_color = 0xEC0000
            kill_icon_url = self.kill_icon_loss
        
        ## Override and overwrite embed defaults with Victory layout.
        if KillerName.strip().lower() in self.requiredPlayers:
            embed_color = 0x00FF00
            kill_icon_url = self.kill_icon_win

        ## End of embed default manipulation


        embeds = []

        ## Kill embed creation. 
        embed = Embed(
            color=embed_color,
            timestamp=KillDataExport['time']#,
        )

        # imageFile = discord.File(f"export_images/{kill_image_name}.png", filename=f"{kill_image_name}.png")
        embed.set_author(name=f"{KillDataExport['killer']} killed {KillDataExport['victim']}", icon_url=kill_icon_url)
        embed.set_image(url=f'{killImageURL}')

        embeds.append(embed)
        ## End of Kill Embed.

        ## Inventory embed creation
        if len (VictimInventory) > 0 and not inventoryURL == None:
            embed = Embed(
                color=embed_color,
                timestamp=KillDataExport['time']#,
            )

            embed.set_author(name=f"{KillDataExport['victim']}'s inventory.")
            embed.set_image(url=f'{inventoryURL}')

            embeds.append(embed)
        ## End of inventory Embed. Message should be sent.

        return embeds

    def SpeedRunData(self, data):
        """ Goes through all the data looking for relevent players/guilds/alliances """
        
        requiredData = []

        player_types = ['Killer', 'Victim']
        for datum in data:
            for player in player_types:
                if datum[player]['AllianceName'].strip().lower() in self.requiredAlliances:
                    if not datum in requiredData:
                        requiredData.append(datum)
                if datum[player]['GuildName'].strip().lower() in self.requiredGuilds:
                    if not datum in requiredData:
                        requiredData.append(datum)
                if datum[player]['Name'].strip().lower() in self.requiredPlayers:
                    if not datum in requiredData:
                        requiredData.append(datum)

        return requiredData

    def ParseItems(self, KillDataExport, killData):
        """ Adds relevent item information onto the KillDataExport object """
        KillerItems = []
        VictimItems = []

        KillDataExport['kIP'] = round(float(killData['Killer']['AverageItemPower']))
        KillDataExport['vIP'] = round(float(killData['Victim']['AverageItemPower']))

        KillDataExport['kEquipment'] = {}
        KillDataExport['vEquipment'] = {}

        for key, value in killData['Killer']['Equipment'].items():
            if not value == None:
                KillDataExport['kEquipment'][key] = (value['Type'], value['Quality'], value['Count'])
        
        for key, value in killData['Victim']['Equipment'].items():
            if not value == None:
                KillDataExport['vEquipment'][key] = (value['Type'], value['Quality'], value['Count'])

        KillDataExport['kInventory'] = []
        KillDataExport['vInventory'] = []

        for item in killData['Killer']['Inventory']:
            if not item == None:
                KillDataExport['kInventory'].append((item['Type'], item['Quality'], item['Count']))

        for item in killData['Victim']['Inventory']:
            if not item == None:
                KillDataExport['vInventory'].append((item['Type'], item['Quality'], item['Count']))

        return KillDataExport

    def ParseKill(self, killData):
        """ Creates a KillDataExport object that contains relevent information about a given kill """
        KillDataExport = {}

        if int(killData['TotalVictimKillFame']) == 0:
            return KillDataExport, False
        
        KillDataExport['time'] = dateutil.parser.isoparse(killData['TimeStamp'])

        KillDataExport['fame'] = killData['TotalVictimKillFame']

        KillDataExport['killer'] = killData['Killer']['Name']
        KillDataExport['kGuild'] = killData['Killer']['GuildName']
        KillDataExport['kAlliance'] = killData['Killer']['AllianceName']

        KillDataExport['victim'] = killData['Victim']['Name']
        KillDataExport['vGuild'] = killData['Victim']['GuildName']
        KillDataExport['vAlliance'] = killData['Victim']['AllianceName']

        KillDataExport['nAssists'] = killData['numberOfParticipants']

        KillDataExport = self.ParseItems(KillDataExport, killData)
        return KillDataExport, True   

    def GetSampleData(self, limit=51, offset=0):
        response = requests.get(f'https://gameinfo.albiononline.com/api/gameinfo/events?limit={limit}&offset={offset}')
        DataResponse = response.json()
        return DataResponse[0]

    def ReduceSpaceUsed(self, start_path='./'):
        """ Removes images from the specified path, in order to reduce total space used by the program """
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    if ".png" in fp[-4:]:
                        total_size += os.path.getsize(fp)

        total_size = total_size / 1e-6

        if total_size > 10.0:
            for filename in os.listdir(start_path):
                file_path = os.path.join(start_path, filename)
                if ".png" in file_path[-4:]:
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print('Failed to delete %s. Reason: %s' % (file_path, e))
        return total_size