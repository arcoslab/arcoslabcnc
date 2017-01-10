#!/usr/bin/python

import pygame
import sys

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() < 1:
    print "No joystick connected, exiting"
    sys.exit(0)

print "Using first joystick"

js=pygame.joystick.Joystick(0)

js.init()

print "Using joystick: ", js.get_name()

finish=False
while not finish:
    for event in pygame.event.get():
        #print "Event: ", event
        if (event.type == pygame.JOYBUTTONDOWN) or (event.type == pygame.JOYBUTTONUP):
            print "Button pressed/released: ", event.button
            print "Button value: ", event.button, js.get_button(event.button)
        if event.type == pygame.JOYAXISMOTION:
            if (event.axis==1) or (event.axis==2) :
                print "Axis changed: ", event.axis
                print "Axis value: ", event.value, js.get_axis(event.axis)



from test import Circle, Axis, Stepper
import sys

motx=Stepper(25, 8, 7)
moty=Stepper(14, 15, 18)
axisx=Axis(motx)
axisy=Axis(moty)
axisx.enable()
axisy.enable()

print sys.argv

if len(sys.argv)<4:
    speed=0.002
else:
    speed=float(sys.argv[3])

axisx.move(float(sys.argv[1]), speed)
axisy.move(float(sys.argv[2]), speed)
while axisx.is_moving():
    print "Waiting for X"
while axisy.is_moving():
    print "Waiting for Y"

axisx.disable()
axisy.disable()
