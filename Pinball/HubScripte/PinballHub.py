from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.iodevices import XboxController
from pybricks.parameters import Port, Stop, Button, Direction
from pybricks.tools import wait, run_task, multitask, 
from allow_missing_motors import Motor
from usys import stdin, stdout
from uselect import poll

keyboard = poll()
keyboard.register(stdin)

hub = PrimeHub()
lFlipper = Motor(Port.C, Direction.COUNTERCLOCKWISE)
rFlipper = Motor(Port.D)
plungerReload = Motor(Port.B, Direction.COUNTERCLOCKWISE)
plunger = Motor(Port.F)
#plungerStopTrigger = ColorSensor(Port.E)
#plungerStartTrigger = ColorSensor(Port.E)
controller = XboxController()

lTargetAngle = 27
rTargetAngle = 27
run = False

defaultAngleL = lFlipper.angle()
defaultAngleR = rFlipper.angle()

#lFlipper.control.limits(torque=450)
#lFlipper.control.limits(acceleration=20000)
#rFlipper.control.limits(torque=450)
#rFlipper.control.limits(acceleration=20000)


lAngleTest = 0
rAngleTest = 0
pb0 = False
spbr = False

async def flipLinksTest():
    global lAngleTest
    lAngleTest = 50
    print(lAngleTest)
async def flipRightTest():
    global rAngleTest
    rAngleTest = 50
    print(rAngleTest)
async def flipLinksResetTest():
    global lAngleTest
    lAngleTest = 0
    print(lAngleTest)
async def flipRightResetTest():
    global rAngleTest
    rAngleTest = 0
    print(rAngleTest)

        
async def main():
    global lAngleTest
    global rAngleTest
    global pb0
    global pbg
    global spbr
    pb0 = False
    pbg = False
    spbr = False

    while True:
        await wait(100)
        stdout.buffer.write(b"pbr")
        cmd = stdin.buffer.read(3)
        #cmd = b"btr"
        if cmd == b"btr":
            run = True
            while run:
                await wait(100)
                if Button.MENU in controller.buttons.pressed():
                    stdin.buffer.write(b"pbs")
                    run = False
                    pbg = True
        while pbg:
            await wait(1)
            if Button.LB in controller.buttons.pressed() and Button.RB in controller.buttons.pressed() and lAngleTest and rAngleTest == 0:
                #multitask(lFlipper.run_angle(10000, 27, Stop.COAST), rFlipper.run_angle(10000, 27, Stop.COAST))
                await multitask(flipLinksTest(), flipRightTest())

            if Button.LB in controller.buttons.pressed() and lAngleTest == 0:
                #lFlipper.run_angle(10000, 27, Stop.COAST)
                await flipLinksTest()

            if Button.LB not in controller.buttons.pressed() and lAngleTest == 50:
                await flipLinksResetTest()
                #lFlipper.run_angle(10000, -27, Stop.COAST)

            if Button.RB in controller.buttons.pressed() and rAngleTest == 0:
                await flipRightTest()
            
            if Button.RB not in controller.buttons.pressed() and rAngleTest == 50:
                await flipRightResetTest()
            
            if controller.dpad() is 1 and Button.MENU in controller.buttons.pressed() and Button.VIEW in controller.buttons.pressed() and pb0 is False:
                pb0 = True
                stdout.buffer.write(b"r?r")
                await wait(1000)

            if controller.dpad() is 0 and Button.MENU not in controller.buttons.pressed() and Button.VIEW not in controller.buttons.pressed() and pb0 is True:
                pb0 = False
            
            stdout.buffer.write(b"r?0")
            cmd = stdin.buffer.read(3)
            if cmd == b"r?1":
                pbg = False
                spbr = False
                #lFlipper.run_angle(10000, -27, Stop.COAST)
                # rFlipper.run_angle(10000, 27, Stop.COAST)
                #wait(0.1)
                #rFlipper.run_angle(10000, -27, Stop.COAST)                
            #if Button.A in controller.buttons.pressed():
                #plunger.run_angle(500, 360*3, Stop.COAST)
            #if Button.B in controller.buttons.pressed():
                #plungerReload.run_angle(800, 360, Stop.NONE)

run_task(main())

