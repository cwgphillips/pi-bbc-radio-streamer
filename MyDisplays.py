from random import randint
import sys, os
import time
import ST7789 as ST7789
from PIL import Image, ImageDraw
from colorsys import hsv_to_rgb
import cairosvg

class SqauareDisplay:
    """This handles the display
    """
    WIDTH = 240
    HEIGHT = WIDTH
    image = None

    def __init__(self) -> None:

        self.disp = ST7789.ST7789(
            height=240,
            rotation=90,
            port=0,
            cs=ST7789.BG_SPI_CS_FRONT,  # BG_SPI_CS_BACK or BG_SPI_CS_FRONT
            dc=9,
            backlight=13,               # 18 for back BG slot, 19 for front BG slot.
            spi_speed_hz=80 * 1000 * 1000,
            offset_left=0,
            offset_top=0
        )
        self.disp.begin()


    def show(self, image_path):
        self.image = self._parseImagePath(image_path)
        self.disp.display(self.image)

    def show_composite(self, mainImagePath, upperLeftPath, upperRightPath, lowerLeftPath, lowerRightPath):
        imageMain = self._parseImagePath(mainImagePath)
        imageUppLeft = self._parseImagePath(upperLeftPath)
        imageUppRight = self._parseImagePath(upperRightPath)
        imageLowLeft = self._parseImagePath(lowerLeftPath)
        imageLowRight = self._parseImagePath(lowerRightPath)
        imageUppLeft = imageUppLeft.resize((50,50))
        imageUppRight = imageUppRight.resize((50,50))
        imageLowLeft = imageLowLeft.resize((50,50))
        imageLowRight = imageLowRight.resize((50,50))

        imageMain.paste(imageUppLeft, (0,0), imageUppLeft)
        imageMain.paste(imageUppRight, (190,0), imageUppRight)
        imageMain.paste(imageUppLeft, (0,0), imageUppLeft)
        imageMain.paste(imageLowLeft, (0,190), imageLowLeft)
        imageMain.paste(imageLowRight, (190,190), imageLowRight)
        
        self.image = imageMain
        self.disp.display(self.image)

    def _parseImagePath(self, image_path):
        if image_path[:4]=="http":
            return self.get_from_url(image_path)
        elif image_path[-4:] == '.png':
            return self.get_from_file(image_path)
        elif image_path.lower()=='pause':
            base = Image.new("RGBA",(self.WIDTH, self.HEIGHT),(255,255,255,0))
            imPause = ImageDraw.Draw(base)
            imPause.rectangle([10, 190, 20, 230], fill="#800080", outline ="green")
            imPause.rectangle([30, 190, 40, 230], fill="#800080", outline ="green")
            return base
        elif image_path.lower()=='mute':
            base = Image.new("RGBA",(self.WIDTH, self.HEIGHT),(255,255,255,0))
            imMute = ImageDraw.Draw(base)
            imMute.line([(20, 10), (200, 230)], fill="red", width=20)
            imMute.line([(220, 10), (40, 230)], fill="red", width=20)            
            return base

        elif image_path==None:
            return None 

    def get_from_file(self, image_file_name_in):
        image = Image.open(image_file_name_in)
        return image.resize((self.WIDTH, self.HEIGHT))

    def get_from_url(self, image_url_in):
        print(f"{image_url_in}")
        image_type = image_url_in[-4:]
        downloaded_image = f"downloaded_image{image_type}"
        os.system(f"curl -o {downloaded_image} {image_url_in}")

        if image_type==".svg":
            imageToShowPath = self.my_svg2png(downloaded_image)
        else:
            imageToShowPath = downloaded_image

        print(f"Loading image: {imageToShowPath}")                        
        image = Image.open(imageToShowPath)
        # image = Image.open("downloaded_image.svg2.png")
        image = image.resize((self.WIDTH, self.HEIGHT))
        return image

    def my_svg2png(self, svgImagePath):
        pngImageOutPath = svgImagePath+"2.png"
        cairosvg.svg2png(url=svgImagePath, write_to=pngImageOutPath)
        return pngImageOutPath
        

