import os, sys
import requests
import shutil
import math
import PIL

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import cloudinary
import cloudinary.uploader
import cloudinary.api


class ImageManipulator:

    def __init__ (self, cloud_name, api_key, api_secret, ImagePath='./', ExportPath='./'):

        cloudinary.config(cloud_name=cloud_name,
                  api_key=api_key,
                  api_secret=api_secret)

        self.MaxInventoryItems = 7
        self.InventoryItemOffset = 98
        self.InventoryStartX = 0
        self.InventoryStartY = -3

        self.ImagePath = ImagePath
        self.ExportPath = ExportPath
        self.image_url = 'https://render.albiononline.com/v1/item/XYZ?quality=QQQ'

        self.BackgroundImage = Image.open(f'data/albionback.png')
        self.InventoryImage = Image.open(f'data/inventory.png')

        self.PlayerFont = ImageFont.truetype("data/LSANS.TTF", 45)
        self.GuildFont = ImageFont.truetype("data/LSANS.TTF", 40)
        self.IPFont = ImageFont.truetype("data/LSANS.TTF", 40)

        self.KillerNamePosition = (154, 45)
        self.KillerGuildPosition = (40, 100)

        self.VictimNamePosition = (1154, 45)
        self.VictimGuildPosition = (1040, 100)

        self.KillerIPPosition = (450, 900)
        self.VictimIPPosition = (1050, 900)

        self.KillFamePosition = (725, 690)
        self.KillFameDividePosition = (725, 750)

        self.KillerEquipmentPositions = {
            "MainHand": (0, 400),
            "OffHand": (400, 400),
            "Head": (200, 180),
            "Armor": (200, 380),
            "Shoes": (200, 580),
            "Bag": (0, 200),
            "Cape": (400, 200),
            "Mount": (200, 770),
            "Potion": (400, 600),
            "Food": (0, 600),
        }

        self.VictimEquipmentPositions = {
            "MainHand": (1000, 400),
            "OffHand": (1400, 400),
            "Head": (1200, 180),
            "Armor": (1200, 380),
            "Shoes": (1200, 580),
            "Bag": (1000, 200),
            "Cape": (1400, 200),
            "Mount": (1200, 770),
            "Potion": (1400, 600),
            "Food": (1000, 600),
        }

    def GetImage(self, ImageName):
        # ImageName should come with extension.
        image = Path(f'{self.ImagePath}/{ImageName}')
        if image.is_file():
            return Image.open(f'{self.ImagePath}/{ImageName}')
        else:
            item = "-".join(ImageName.split('-')[:-1])
            quality = ImageName.split('-')[-1].split('.')[0]

            image_url = self.image_url.replace('XYZ', item)
            image_url = image_url.replace('QQQ', quality)

            r = requests.get(image_url, stream = True)
            if r.status_code == 200:
                r.raw.decode_content = True

                with open(f'{self.ImagePath}/{ImageName}','wb') as f:
                    shutil.copyfileobj(r.raw, f)

                if image.is_file():
                    return Image.open(f'{self.ImagePath}/{ImageName}')
                else:
                    print (f'[ERR] Image Downloaded, but could not be opened')
            else:
                print (f'[ERR] Failed obtaining image')

        return None

    def InsertText (self, backgroundImage, PlayerName, PlayerGuild, PlayerIP, KillFame = None, AssistNum=None, color=(22, 22, 22), killer=True):
        if killer:
            NamePosition = self.KillerNamePosition
            GuildPosition = self.KillerGuildPosition
            IPPosition = self.KillerIPPosition
        else:
            NamePosition = self.VictimNamePosition
            GuildPosition = self.VictimGuildPosition
            IPPosition = self.VictimIPPosition
        
        NameFont = self.PlayerFont
        GuildFont = self.GuildFont
        IPFont = self.IPFont
        KillFamePosition = self.KillFamePosition
        FameDividePosition = self.KillFameDividePosition


        draw = ImageDraw.Draw(backgroundImage)
        draw.text(NamePosition, PlayerName, color, font=NameFont)
        draw.text(GuildPosition, PlayerGuild, color, font=GuildFont)

        draw.text(IPPosition, f'IP: {PlayerIP}', color, font=IPFont)
        if not KillFame == None:
            draw.text(KillFamePosition, f'F: {KillFame}', color, font=IPFont)
            
            if AssistNum == None or AssistNum <= 0:
                AssistNum = 1
            FameDivided = math.floor(KillFame/AssistNum)
            draw.text(FameDividePosition, f'{AssistNum}x {FameDivided}', color, font=IPFont)

        return backgroundImage


    def InsertEquipment (self, backgroundImage, Equipment, killer=True):

        for key, value in Equipment.items():
            ItemName = value[0]
            ItemQuality = value[1]
            ItemCount = value[2]

            ImageName = f'{ItemName}-{ItemQuality}.png'

            image = self.GetImage(ImageName)


            if image == None:
                continue
            
            font = ImageFont.truetype("data/LSANS.TTF", 30)
            draw = ImageDraw.Draw(image)
            msg = f'{ItemCount}'
            draw.text((image.size[0] - 60, image.size[1] - 75), msg,(225, 225, 225),font=font)

            
            if killer:
                image_paste_position = self.KillerEquipmentPositions[key]
            else:
                image_paste_position = self.VictimEquipmentPositions[key]

            backgroundImage.paste(image, image_paste_position, image)

        return backgroundImage

    def ConcatenateVertically(self, im1, im2):
        dst = Image.new('RGB', (im1.width, im1.height + im2.height))
        dst.paste(im1, (0, 0))
        dst.paste(im2, (0, im1.height))
        return dst

    def CreateInventory (self, inventoryItems):
        row = []
        # nRows = math.ceil(len(inventoryItems) / (self.MaxInventoryItems + 1))

        currentRow = None
        for itemIndex, item in enumerate(inventoryItems):
            ItemName = item[0]#['Type']
            ItemQuality = item[1]#['Quality']
            ItemCount = item[2]

            ImageName = f'{ItemName}-{ItemQuality}.png'

            image = self.GetImage(ImageName)

            if image == None:
                continue

            font = ImageFont.truetype("data/LSANS.TTF", 30)
            draw = ImageDraw.Draw(image)
            msg = f'{ItemCount}'
            draw.text((image.size[0] - 60, image.size[1] - 75), msg,(225, 225, 225),font=font)
            
            ## Resize image to fil the inventory
            maxsize = math.floor(image.size[0] * 0.49), math.floor(image.size[1] * 0.49)
            image.thumbnail(maxsize, PIL.Image.ANTIALIAS)
            ##

            InventoryPosition = itemIndex % self.MaxInventoryItems
            if InventoryPosition == 0 and currentRow == None:
                currentRow = self.InventoryImage.copy()
            
            ItemPositionX = self.InventoryStartX + self.InventoryItemOffset * InventoryPosition
            ItemPositionY = self.InventoryStartY

            currentRow.paste(image, (ItemPositionX, ItemPositionY), image)

            
            if InventoryPosition == self.MaxInventoryItems - 1:
                row.append(currentRow)
                currentRow = None

        if not currentRow == None:
            row.append(currentRow)
            currentRow = None

        mainInventory = row[0]

        for i, r in enumerate(row):
            if not i == 0:
                mainInventory = self.ConcatenateVertically(mainInventory, r)    
        
        return mainInventory

        

    def SaveImage(self, image, name, ext='png'):
        image.save(f'./{name}.{ext}', quality=95)
        return f'./{name}.{ext}'

    def UploadImage(self, ImagePath, ImageName):
        res = cloudinary.uploader.upload(f"{ImagePath}", public_id=f'{ImageName}')
        return res['url'], res['public_id']

    def DeleteImages(self, ImagesToDelete):
        cloudinary.api.delete_resources(ImagesToDelete)

    def DeleteImageLocally(self, imageDeletePath):
        if os.path.isfile(imageDeletePath):
            os.unlink(imageDeletePath)

    def GetBlankBackground (self):
        return self.BackgroundImage.copy()
        