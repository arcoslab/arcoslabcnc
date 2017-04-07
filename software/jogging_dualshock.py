#!/usr/bin/python

import pygame
import sys

output_port_name="/jogging/cmd:o"
server_input_port_name="/cnc/cmd:i"
scale_factor=0.05 # 0.01m/s (1cm/s) max speed
dead_band=0.1 # dead band between -0.3 and 0.3

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
style=yarp.ContactStyle()
style.persistent=True
yarp.Network.connect(output_port_name, server_input_port_name, style )

max_val=[1.0, 1.0, 1.0]
min_val=[-1.0, -1.0, -1.0]

def quad_scale(data):
    if data<0:
        return(-data**4)
    else:
        return(data**4)

def joy_to_distance(data):
    return(quad_scale(data)*scale_factor)

def dead_band_transform(data):
    if (data > dead_band):
        #print "up side"
        out=(data-dead_band)/(1.0-dead_band)
    elif (data < -dead_band):
        #print "down side"
        out=(data+dead_band)/(1.0-dead_band)
    else:
        #print "Dead band"
        out=0.0
    #print "Dead band adjustment: ", data, out
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

def scale_cal(data, axis):
    if data<0.0:
        return(data/-min_val[axis])
    elif data>0.0:
        return(data/max_val[axis])
    else:
        return(0.0)

finish=False
active=True
speed=[0.0, 0.0, 0.0]
while not finish:
    pygame.event.get()
    button_value=js.get_button(11)
    if button_value==0:
        active=False
    else:
        active=True

    for axis in [1,2,3]:
        value=js.get_axis(axis)
        print "Updating speed value", axis, value
        if axis==1:
            if value>0:
                if value>max_val[2]:
                    print "Increasing max_val for Z", value
                    max_val[2]=value
            else:
                if value<min_val[2]:
                    print "Decreasing min_val for Z", value
                    min_val[2]=value
            speed[2]=joy_to_distance(dead_band_transform(scale_cal(value, 2)))
        elif axis==2:
            if value>0:
                if value>max_val[0]:
                    print "Increasing max_val for X", value
                    max_val[0]=value
            else:
                if value<min_val[0]:
                    print "Decreasing min_val for X", value
                    min_val[0]=value
            speed[0]=joy_to_distance(dead_band_transform(scale_cal(value, 0)))
        elif axis==3:
            if value>0:
                if value>max_val[1]:
                    print "Increasing max_val for Y", value
                    max_val[1]=value
            else:
                if value<min_val[1]:
                    print "Decreasing min_val for Y", value
                    min_val[1]=value
            speed[1]=joy_to_distance(dead_band_transform(scale_cal(value, 1)))


    if not active:
        speed=[0.0, 0.0, 0.0]
    #print "Sending control command: ", speed
    output_bottle=output_port.prepare()
    output_bottle.clear()
    output_bottle.addString("speed "+str(speed[0])+" "+str(speed[1])+" "+str(speed[2])) #speed in meters per second
    output_port.write()
    yarp.Time.delay(0.001)



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
