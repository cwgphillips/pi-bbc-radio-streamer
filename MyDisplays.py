import os
import ST7789 as ST7789
from PIL import Image, ImageDraw
import cairosvg

class SqauareDisplay:
    """This handles the display
    """
    WIDTH = 240
    HEIGHT = WIDTH
    DIR_DOWNLOADED_IMAGES = "downloaded_images"
    image = None

    icon_urls = {
        "pause": "https://www.reshot.com/preview-assets/icons/4NK7FC936B/pause-4NK7FC936B.svg",
        "mute": "https://www.reshot.com/preview-assets/icons/42HMZ5DWA7/mute-42HMZ5DWA7.svg",
        "unmute": "https://www.reshot.com/preview-assets/icons/RHD29KPNSA/volume-RHD29KPNSA.svg",
        "play": "https://www.reshot.com/preview-assets/icons/M5CZEU4XWN/play-M5CZEU4XWN.svg",
        "stop": "https://www.reshot.com/preview-assets/icons/6TMKY3BGJX/stop-6TMKY3BGJX.svg",
    }


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
        if type(image_path) is list or type(image_path) is tuple:
            if image_path[0][:4]=="http":
                return self.get_from_url(image_path)
            if image_path[0][-4:] == '.png':
                return self.get_from_file(image_path)
            if image_path[0].lower() in list(self.icon_urls.keys()):
                return self.get_from_url((self.icon_urls[image_path[0].lower()],image_path[1]))

        elif image_path.lower() in list(self.icon_urls.keys()):
            return self.get_from_url((self.icon_urls[image_path.lower()],image_path))

        elif image_path.lower()=='blank':
            base = Image.new("RGBA",(self.WIDTH, self.HEIGHT),(0,0,0,0))
            ImageDraw.Draw(base)
            return base

        elif image_path is None:
            return None


    def get_from_file(self, image_file_name_in):
        image = Image.open(image_file_name_in)
        return image.resize((self.WIDTH, self.HEIGHT))


    def get_from_url(self, image_url_in):
        testDoesImageAlreadyExistLocally = f"{self.DIR_DOWNLOADED_IMAGES}/{image_url_in[1]}.png"
        if os.path.exists(testDoesImageAlreadyExistLocally):
            print(f"\t### Image exists... {testDoesImageAlreadyExistLocally}")
            imageToShowPath = testDoesImageAlreadyExistLocally
        else:
            print(f"\t### Image does not exist... {testDoesImageAlreadyExistLocally}")
            image_type = os.path.splitext(os.path.basename(image_url_in[0]))[1]
            if not os.path.exists(self.DIR_DOWNLOADED_IMAGES):
                os.mkdir(self.DIR_DOWNLOADED_IMAGES)
            downloaded_image = f"{self.DIR_DOWNLOADED_IMAGES}/{image_url_in[1]}{image_type}"
            print(f"downloaded_image = {downloaded_image}")
            os.system(f"curl -o {downloaded_image} {image_url_in[0]}")

            if image_type==".svg":
                imageToShowPath = self.my_svg2png(downloaded_image)
            else:
                imageToShowPath = downloaded_image

        print(f"Loading image: {imageToShowPath}")                        

        return self.get_from_file(imageToShowPath)


    def my_svg2png(self, svgImagePath):
        pngImageOutPath = os.path.join(os.path.dirname(svgImagePath),\
             os.path.splitext(os.path.basename(svgImagePath))[0]+".png")
        cairosvg.svg2png(url=svgImagePath, write_to=pngImageOutPath)
        return pngImageOutPath
