#!/usr/bin/python

import pygame
import sys

output_port_name="/jogging/cmd:o"
server_input_port_name="/cnc/cmd:i"
scale_factor=0.01 # 0.01m/s (1cm/s) max speed
dead_band=0.3 # dead band between -0.3 and 0.3

pygame.init()
pygame.joystick.init()
if pygame.joystick.get_count() < 1:
    print "No joystick connected, exiting"
    sys.exit(0)
print "Using first joystick"
js=pygame.joystick.Joystick(0)
js.init()
print "Using joystick: ", js.get_name()

import yarp
yarp.Network.init()
output_port=yarp.BufferedPortBottle()
output_port.open(output_port_name)
yarp.Network.connect(output_port_name, server_input_port_name)

def joy_to_distance(data):
    return(data*scale_factor)

def dead_band_transform(data):
    if (data > dead_band):
        print "up side"
        out=(data-dead_band)/(1.0-dead_band)
    elif (data < -dead_band):
        print "down side"
        out=(data+dead_band)/(1.0-dead_band)
    else:
        print "Dead band"
        out=0.0
    print "Dead band adjustment: ", data, out
    return(out)

def sat(data):
    if abs(data) > 1.0:
        print "Saturating"
        if data <0.0:
            return(-1.0)
        else:
            return(1.0)
    else:
        return(data)

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
                print "Sending value with yarp"
                output_bottle=output_port.prepare()
                output_bottle.clear()
                if event.axis==1:
                    axis="Y"
                else:
                    axis="X"
                output_bottle.addString("speed "+axis+str(joy_to_distance(dead_band_transform(sat(event.value))))) #speed in meters per second
                output_port.write()



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
