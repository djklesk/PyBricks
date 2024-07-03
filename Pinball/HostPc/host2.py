import asyncio
from contextlib import suppress
from bleak import BleakScanner, BleakClient
import sys
import socket
from math import log10, ceil
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import numpy as np
import os.path

PYBRICKS_COMMAND_EVENT_CHAR_UUID = "c5f50002-8280-46da-89f4-6d8051e4aeef"

HUB2_NAME = "Pybrick Hub2"  #scoreboard
HUB_NAME = "Pybrick Hub1"   #pnball
PIXOO_NAME = "Pixoo"
RETRY = False
DISCONNECTCMD = "EXIT"

POINTS = []
POINT = 0

mainHubReady = False

pbhub = None
sbhub = None
pixoo = None

class Pixoo:
    global image_bytes
    global font
    size = 16
    pixel_count = size * size
    CMD_SET_SYSTEM_BRIGHTNESS = 0x74
    font = ImageFont.truetype(r"C:\Users\DJ\AppData\Local\Microsoft\Windows\Fonts\pico.ttf", 5)

    def __init__(self, mac_address):
        self.mac_address = mac_address
        self.btsock = None

    @staticmethod
    def get():
        if Pixoo.instance is None:
            Pixoo.instance = Pixoo(Pixoo.BDADDR)
            Pixoo.instance.connect()
        return Pixoo.instance

    def connect(self):
        self.btsock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.btsock.connect((self.mac_address, 1))

    def __spp_frame_checksum(self, args):
        return sum(args[1:]) & 0xffff

    def __spp_frame_encode(self, cmd, args):
        payload_size = len(args) + 3
        frame_header = [1, payload_size & 0xff, (payload_size >> 8) & 0xff, cmd]
        frame_buffer = frame_header + args
        cs = self.__spp_frame_checksum(frame_buffer)
        frame_suffix = [cs & 0xff, (cs >> 8) & 0xff, 2]
        return frame_buffer + frame_suffix

    def send(self, cmd, args):
        spp_frame = self.__spp_frame_encode(cmd, args)
        if self.btsock is not None:
            self.btsock.send(bytes(spp_frame))

    def set_system_brightness(self, brightness):
        self.send(Pixoo.CMD_SET_SYSTEM_BRIGHTNESS, [brightness & 0xff])

    def encode_image(self, filepath):
        img = Image.open(filepath)
        return self.encode_raw_image(img)

    def encode_raw_image(self, img): 
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

        bitwidth = len(bin(len(palette) - 1)[2:])  # Calculate bit width based on palette size
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
        return len(palette), encoded_palette, encoded_data

        size = (16, 16)
        background_color = (0, 0, 0)
        digit_color = (255, 255, 255)
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

        draw.text(position1, text1, fill=digit_color, font=font)
        draw.text(position2, text2, fill=digit_color, font=font)
        #image.save(f'saved.png')
        image_bytes = BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes.seek(0)  
        return image_bytes

    def draw_gif(self, filepath, speed=1):
            frames = []
            timecode = 0
            anim_gif = Image.open(filepath)
            for n in range(anim_gif.n_frames):
                anim_gif.seek(n)
                nb_colors, palette, pixel_data = self.encode_raw_image(
                    anim_gif.convert(mode='RGB'))
                frame_size = 7 + len(pixel_data) + len(palette)
                frame_header = [
                    0xAA, frame_size & 0xff, (frame_size >> 8) & 0xff,
                    timecode & 0xff, (timecode >> 8) & 0xff, 0, nb_colors
                ]
                frame = frame_header + palette + pixel_data
                frames += frame
                timecode += speed
            # send animation
            nchunks = ceil(len(frames) / 200.)
            total_size = len(frames)
            for i in range(nchunks):
                chunk = [total_size & 0xff, (total_size >> 8) & 0xff, i]
                self.send(0x49, chunk + frames[i * 200:(i + 1) * 200])


    def draw_pic(self, image_bytes):
        img = Image.open(image_bytes)
        nb_colors, palette, pixel_data = self.encode_raw_image(img)
        frame_size = 7 + len(pixel_data) + len(palette)
        frame_header = [0xAA, frame_size & 0xff, (frame_size >> 8) & 0xff, 0, 0, 0, nb_colors]
        frame = frame_header + palette + pixel_data
        prefix = [0x0, 0x0A, 0x0A, 0x04]
        self.send(0x44, prefix + frame)


async def main():
    main_task = asyncio.current_task()
    global pbhub
    global sbhub
    global pixoo
    global sbr
    global pbr
    global pbg
    global r_r
    global r_0
    global ppp
    ppp = False
    r_0 = False
    r_r = False
    sbr = False
    pbr = False
    pbg = False
    ready_event = asyncio.Event()

    async def sendPixooPoint(points):
        pixoo.draw_pic(POINTS[POINT])

    async def hide_showRobotGif(show = True):
        if show:            
            pixoo.draw_gif(r"C:\Users\DJ\Documents\coding\pixoo-client\winking_robot.gif")
        else:
            print(0)
            pixoo.draw_pic(await sendPixooPoint(0))
    
    async def hide_showFireworks(show = True):
        if show:            
            pixoo.draw_gif(r"C:\Users\DJ\Documents\coding\pixoo-client\fireworks show.gif")
        else:            
            pixoo.draw_pic(await sendPixooPoint(0))

    async def pointRoutine(point):
        targetpoint = 1000
        if point >= targetpoint:
            await sendPixooPoint(point)
        elif point == targetpoint:
            await hide_showFireworks(True)
            await asyncio.sleep(10)

    async def createPointsArray(maxPoints):
        imgarray = []
        for i in range(0,maxPoints):
            imgarray.append(await createPixooPoint(i))
        imgarray = np.array(imgarray)
        np.save(r'C:\Users\DJ\Documents\coding\pixoo-client\array_data.npy', imgarray)       







































































        
   
    async def createPixooPoint(points):
        digit_image = None
        if points < 999:
            digit_image = createImg(points, "")
        else:
            digit_image = createImg(f"{points // 1000}k", points % 1000)
        return digit_image
    
    def createImg(digit1, digit2):
        size = (16, 16)
        background_color = (0, 0, 0)
        digit_color = (255, 255, 255)
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
        draw.text(position1, text1, fill=digit_color, font=font)
        draw.text(position2, text2, fill=digit_color, font=font)
        image_bytes = BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes.seek(0)  
        return image_bytes
    
    def handle_disconnect(_):
        print("Hub was disconnected.")
        if not main_task.done():
            main_task.cancel()

    def handle_rxsb(_, data: bytearray):
        global sbr
        global ppp
        global POINTS
        if data[0] == 0x01:  # "write stdout" event (0x01)
            payload = data[1:]
            if payload == b"sbr":
                print("sb connected")
                sbr = True
                ready_event.set()
            elif payload[:3] == b"pbp":
                payload = payload[3:]
                POINT = int((payload))
                ppp = True
                ready_event.set()
            elif payload == b"r?0":
                r_0 = True
                ready_event.set()
            else:
                print("Received:", payload)

    def handle_rxpb(_, data: bytearray):
        global POINTS
        global pbr
        global pbg
        global r_r
        global r_0
        if data[0] == 0x01:  # "write stdout" event (0x01)
            payload = data[1:]
            if payload == b"pbr":
                print("pb connected")
                pbr = True
                ready_event.set()
            elif payload == b"pbs":
                print("pb started")
                pbg = True
                ready_event.set()
            elif payload == b"r?r":
                print("pb started")
                r_r = True
                ready_event.set()
            elif payload == b"r?0":
                r_0 = True
                ready_event.set()

            else:
                print("Received:", payload)

    def detection_callback(device, advertising_data):
        global pbhub
        global sbhub
        global pixoo
        data = []
        if device.name is not None:            
            if pbhub is None and device.name.lower() == HUB_NAME.lower():
                pbhub = BleakClient(device, handle_disconnect)
            elif pbhub is None and device.name.lower() == HUB2_NAME.lower():
                sbhub = BleakClient(device, handle_disconnect)

    if os.path.exists('array_data.npy'):
        POINTS = np.load('array_data.npy')
    else:
        await createPointsArray(1000)

    for i in range(1,4):
        global pbhub
        global sbhub
        global pixoo
        async with BleakScanner(detection_callback, service_uuids=["c5f50001-8280-46da-89f4-6d8051e4aeef"]) as scanner:
            await asyncio.sleep(0.1)
            devs = scanner.discovered_devices
        if pbhub and sbhub is not None:
            break
        await asyncio.sleep(0.25)

    pix = await BleakScanner.find_device_by_name("Pixoo")
    if pix != None:
        pixoo = Pixoo(pix.address)

    if pbhub is None: #<------------------------------------- add later second hub
        print(f"could not find pbhub with name: {HUB_NAME}")
        return
    else:
        print(f"found hub with name: {HUB_NAME}")
    
    if sbhub is None: #<------------------------------------- add later second hub
        print(f"could not find pbhub with name: {HUB2_NAME}")
        return
    else:
        print(f"found hub with name: {HUB2_NAME}")

    if pixoo is None:
        print(f"could not find hub with name: Pixoo")
    else:
        print(f"found Pixoo")
        pixoo.connect()
        await hide_showRobotGif()

    

    if pbhub and sbhub is not None:
        await pbhub.connect()
        await pbhub.start_notify(PYBRICKS_COMMAND_EVENT_CHAR_UUID, handle_rxpb)
        await sbhub.connect()
        await sbhub.start_notify(PYBRICKS_COMMAND_EVENT_CHAR_UUID, handle_rxsb)
            
    async def sendsb(data):
        try:
            await sbhub.write_gatt_char(PYBRICKS_COMMAND_EVENT_CHAR_UUID, b"\x06" + data, response=True)
        finally:
            return
        
    async def sendpb(data):
        try:
            await pbhub.write_gatt_char(PYBRICKS_COMMAND_EVENT_CHAR_UUID, b"\x06" + data, response=True)
        finally:
            return
 

    print("Start the controller and press the button on both hubs")

    while True:
        await ready_event.wait()
        ready_event.clear()
        if pbr and sbr:
            await sendpb(b"btr")
            pbr = False
            sbr = False
        if pbg:         
            await sendpb(b"pbg")
            await sendsb(b"pbg")
            pbg = False
        if r_r:
            r_r = False
            await sendsb(b"r?1")
            await sendpb(b"r?1")
        if r_0 == True:
            r_0 = False
            await sendpb(b"000")
        if ppp == True:
            ppp = False
            await pointRoutine(POINT)###PB ROUTINE ADD!!!!! line311
            await sendsb(b"000")

        EXIT = False
        if EXIT == True:
            await sendsb(b"bye")
            sys.exit(1)


if __name__ == "__main__":

    with suppress(asyncio.CancelledError):
        asyncio.run(main())
