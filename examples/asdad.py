"""
Pixoo 
"""

import sys
import socket
from time import sleep
from binascii import unhexlify, hexlify
from math import log10, ceil
from enum import IntEnum
from PIL import Image, ImageOps
from rich.text import Text
from rich.console import Console
from PIL import Image, ImageDraw, ImageFont


console = Console()
def clamp(value, minimum=0, maximum=255):
    return max(minimum, min(value, maximum))

def clamp_color(rgb):
    return clamp(rgb[0]), clamp(rgb[1]), clamp(rgb[2])

def round_location(xy):
    return round(xy[0]), round(xy[1])

class Palette:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
class Pixoo(object):
  size = 16
  pixel_count = size * size
  __buffer = [0] * (pixel_count * 3)
  CMD_SET_SYSTEM_BRIGHTNESS = 0x74
  CMD_SPP_SET_USER_GIF = 0xb1
  CMD_DRAWING_ENCODE_PIC = 0x5b

  BOX_MODE_CLOCK=0
  BOX_MODE_TEMP=1
  BOX_MODE_COLOR=2
  BOX_MODE_SPECIAL=3

  instance = None

  def __init__(self, mac_address):
    """
    Constructor
    """
    self.mac_address = mac_address
    self.btsock = None


  @staticmethod
  def get():
    if Pixoo.instance is None:
      Pixoo.instance = Pixoo(Pixoo.BDADDR)
      Pixoo.instance.connect()
    return Pixoo.instance

  def connect(self):
    """
    Connect to SPP.
    """
    self.btsock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    self.btsock.connect((self.mac_address, 1))


  def __spp_frame_checksum(self, args):
    """
    Compute frame checksum
    """
    return sum(args[1:])&0xffff


  def __spp_frame_encode(self, cmd, args):
    """
    Encode frame for given command and arguments (list).
    """
    payload_size = len(args) + 3

    # create our header
    frame_header = [1, payload_size & 0xff, (payload_size >> 8) & 0xff, cmd]

    # concatenate our args (byte array)
    frame_buffer = frame_header + args

    # compute checksum (first byte excluded)
    cs = self.__spp_frame_checksum(frame_buffer)

    # create our suffix (including checksum)
    frame_suffix = [cs&0xff, (cs>>8)&0xff, 2]

    # return output buffer
    return frame_buffer+frame_suffix


  def send(self, cmd, args):
    """
    Send data to SPP.
    """
    spp_frame = self.__spp_frame_encode(cmd, args)
    if self.btsock is not None:
      nb_sent = self.btsock.send(bytes(spp_frame))


  def set_system_brightness(self, brightness):
    """
    Set system brightness.
    """
    self.send(Pixoo.CMD_SET_SYSTEM_BRIGHTNESS, [brightness&0xff])


  def set_box_mode(self, boxmode, visual=0, mode=0):
    """
    Set box mode.
    """
    self.send(0x45, [boxmode&0xff, visual&0xff, mode&0xff])


  def set_color(self, r,g,b):
    """
    Set color.
    """
    self.send(0x6f, [r&0xff, g&0xff, b&0xff])

  def encode_image(self, filepath):
    img = Image.open(filepath)
    return self.encode_raw_image2(img)

  

  def get_pixel_art(self, digit1, digit2):
          size = (16, 16)
          background_color = (255, 255, 255)
          digit_color = (0, 0, 0)
          #font = ImageFont.truetype(r"C:\Users\DJ\AppData\Local\Microsoft\Windows\Fonts\pico.ttf", 8)
          font = ImageFont.truetype(r"C:\Users\DJ\AppData\Local\Microsoft\Windows\Fonts\pico.ttf", 5)
          image = Image.new("RGB", size, background_color)
          draw = ImageDraw.Draw(image)
          text1 = str(digit1)
          text2 = str(digit2)
          
          bbox1 = draw.textbbox((0, 0), text1, font=font)
          width1, height1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]
          position1 = ((size[0] - width1) // 2, (size[1] // 2 - height1) // 2)
          
          bbox2 = draw.textbbox((0, 0), text2, font=font)
          width2, height2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
          position2 = ((size[0] - width2) // 2, size[1] // 2 + (size[1] // 2 - height2) // 2)
        # Draw the digits
          draw.text(position1, text1, fill=digit_color, font=font)
          draw.text(position2, text2, fill=digit_color, font=font)
          image.save(f'saved.png')
          return image

 

  def encode_raw_image(self, img):
    w, h = img.size
    if w == h:
        if w > 16:
            img = img.resize((16, 16))
        
        pixels = []
        palette = []
        for y in range(16):
            for x in range(16):
                pix = img.getpixel((x, y))
                if len(pix) == 4:
                    r, g, b, a = pix
                elif len(pix) == 3:
                    r, g, b = pix
                if (r, g, b) not in palette:
                    palette.append((r, g, b))
                    idx = len(palette) - 1
                else:
                    idx = palette.index((r, g, b))
                pixels.append(idx)

        bitwidth = ceil(log10(len(palette)) / log10(2))
        nbytes = ceil((256 * bitwidth) / 8.0)
        encoded_pixels = [0] * nbytes

        encoded_pixels = []
        encoded_byte = ''
        for i in pixels:
            encoded_byte = bin(i)[2:].rjust(bitwidth, '0') + encoded_byte
            if len(encoded_byte) >= 8:
                encoded_pixels.append(encoded_byte[-8:])
                encoded_byte = encoded_byte[:-8]
        encoded_data = [int(c, 2) for c in encoded_pixels]
        encoded_palette = []
        for r, g, b in palette:
            encoded_palette += [r, g, b]
        return (len(palette), encoded_palette, encoded_data)
    else:
        print('[!] Image must be square.')

  

  def encode_raw_image2(self, img):
    w, h = img.size
    if w == h:
        if w > 16:
            img = img.resize((16, 16))
        
        pixels = []
        palette = []
        for y in range(16):
            for x in range(16):
                pix = img.getpixel((x, y))
                if len(pix) == 4:
                    r, g, b, a = pix
                elif len(pix) == 3:
                    r, g, b = pix
                if (r, g, b) not in palette:
                    palette.append((r, g, b))
                    idx = len(palette) - 1
                else:
                    idx = palette.index((r, g, b))
                pixels.append(idx)

        bitwidth = ceil(log10(len(palette)) / log10(2))
        nbytes = ceil((256 * bitwidth) / 8.0)
        encoded_pixels = [0] * nbytes

        encoded_pixels = []
        encoded_byte = ''
        for i in pixels:
            encoded_byte = bin(i)[2:].rjust(bitwidth, '0') + encoded_byte
            if len(encoded_byte) >= 8:
                encoded_pixels.append(encoded_byte[-8:])
                encoded_byte = encoded_byte[:-8]
        encoded_data = [int(c, 2) for c in encoded_pixels]
        encoded_palette = []
        for r, g, b in palette:
            encoded_palette += [r, g, b]
        return (len(palette), encoded_palette, encoded_data)
    else:
        print('[!] Image must be square.')
      
  def draw_gif(self, filepath, speed=100):
    """
    Parse Gif file and draw as animation.
    """
    # encode frames
    frames = []
    timecode = 0
    anim_gif = Image.open(filepath)
    for n in range(anim_gif.n_frames):
      anim_gif.seek(n)
      nb_colors, palette, pixel_data = self.encode_raw_image(anim_gif.convert(mode='RGB'))
      frame_size = 7 + len(pixel_data) + len(palette)
      frame_header = [0xAA, frame_size&0xff, (frame_size>>8)&0xff, timecode&0xff, (timecode>>8)&0xff, 0, nb_colors]
      frame = frame_header + palette + pixel_data
      frames += frame
      timecode += speed

    # send animation
    nchunks = ceil(len(frames)/200.)
    total_size = len(frames)
    for i in range(nchunks):
      chunk = [total_size&0xff, (total_size>>8)&0xff, i]
      self.send(0x49, chunk+frames[i*200:(i+1)*200])
   

  def draw_anim(self, filepaths, speed=100):
    timecode=0

    # encode frames
    frames = []
    n=0
    for filepath in filepaths:
      nb_colors, palette, pixel_data = self.encode_image(filepath)
      frame_size = 7 + len(pixel_data) + len(palette)
      frame_header = [0xAA, frame_size&0xff, (frame_size>>8)&0xff, timecode&0xff, (timecode>>8)&0xff, 0, nb_colors]
      frame = frame_header + palette + pixel_data
      frames += frame
      timecode += speed
      n += 1
    
    # send animation
    nchunks = ceil(len(frames)/200.)
    total_size = len(frames)
    for i in range(nchunks):
      chunk = [total_size&0xff, (total_size>>8)&0xff, i]
      self.send(0x49, chunk+frames[i*200:(i+1)*200])


  def draw_pic(self, filepath):
    """
    Draw encoded picture.
    """
    nb_colors, palette, pixel_data = self.encode_image(filepath)
    #print(palette)
    frame_size = 7 + len(pixel_data) + len(palette)
    frame_header = [0xAA, frame_size&0xff, (frame_size>>8)&0xff, 0, 0, 0, nb_colors]
    frame = frame_header + palette + pixel_data
    prefix = [0x0, 0x0A,0x0A,0x04]
    self.send(0x44, prefix+frame)

def calcPoint(points):
   if points >=  1000:
      calc = points - 1000
      if calc > 0:
        digit_image = pixoo.get_pixel_art("1k", calc)
      else:
        digit_image = pixoo.get_pixel_art("1k", "")
   else:
        digit_image = pixoo.get_pixel_art(points, "")
   pixoo.draw_pic(r"C:\Users\DJ\Documents\coding\pixoo-client\saved.png")

if __name__ == '__main__':
  if len(sys.argv) >= 3:
    pixoo_baddr = sys.argv[1]
    img_path = sys.argv[2]
    pixoo = Pixoo(pixoo_baddr)
    pixoo.connect()
    for i in range(11):
       if i == 0:
        calcPoint(1)
       else:
        calcPoint(i+997)
        sleep(1)
          
