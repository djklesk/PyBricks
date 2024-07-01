from pybricks.hubs import PrimeHub
from pybricks.pupdevices import ForceSensor, UltrasonicSensor
from pybricks.parameters import Port
from pybricks.tools import wait, run_task, StopWatch
from usys import stdin, stdout
from uselect import poll
import ujson
keyboard = poll()
keyboard.register(stdin)

SensorForce1 = ForceSensor(Port.A)
SensorForce2 = ForceSensor(Port.B)

hub = PrimeHub()

stopwatchForces = StopWatch()
stopwatchSonics = StopWatch()
timeoutStopwatchForces = 2500
timeoutStopwatchSonics = 2500


global points
global run
run = False
points = 0
while True:
    wait(100)
    stdout.buffer.write(b"sbr")
    cmd = stdin.buffer.read(3)
    if cmd == b"pbg":
        run = True
        while run:
            wait(1)
            #print(points)
            stdout.buffer.write(b"pbp"+str(points))
            cmd = stdin.buffer.read(3)
            if SensorForce1.distance() or SensorForce2.distance() > 0.1:
                points += 1
            if cmd == b"r?1":
                print("sb reset")
                points = 0
                run = False
