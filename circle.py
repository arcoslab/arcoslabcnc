#!/usr/bin/python

from math import pi, atan, sin, cos
import sys
motor_step=(0.9, 0.9) #degrees
screw_pitch=(0.005, 0.005) #meters

def frange(x, y, jump):
  while x < y:
    yield x
    x += jump

class Circle:
    def __init__(self, motor_step=(0.9, 0.9), screw_pitch=(0.005, 0.005)):
        self.step_x=motor_step[0]
        self.step_y=motor_step[1]
        self.pitch_x=screw_pitch[0]
        self.pitch_y=screw_pitch[1]
        self.res_x=(self.step_x/360.)*self.pitch_x
        self.res_y=(self.step_y/360.)*self.pitch_y
        self.move_speed=0.05
        self.cut_speed=0.03

    def do_circle(self, radius, cut_speed=0.03, move_speed=0.05):
        cmds=[]
        step_angle=atan(self.res_x/radius)*360.0/(2.*pi)
        print "Step angle: ", step_angle
        old_x=0.0
        old_y=0.0
        iteration=0
        for angle in frange(0., 360.0, step_angle):
            x=radius*cos(angle*(2*pi)/360.0)
            y=radius*sin(angle*(2*pi)/360.0)
            if iteration==0:
                print "Position piece in circle center"
                print "Moving to first circle position, pull bit up!"
                cmds.append("up")
                iteration=1
                speed=move_speed
            elif iteration==1:
                print "Start mill position, pull bit down at desired height!"
                cmds.append("down")
                iteration=2
                speed=cut_speed

            #print "Angle: ", angle, "X, Y: ", x, y, x-old_x, y-old_y
            #raw_input()
            cmds.append("move "+str(x-old_x)+" "+str(y-old_y)+" "+str(speed))
            old_x=x
            old_y=y
        print "Pull bit up!, moving fast to center"
        cmds.append("up")
        speed=move_speed
        cmds.append("move "+str(-radius)+" "+str(0.0)+" "+str(speed))
        return(cmds)

print sys.argv

if len(sys.argv)<2:
    sys.exit(-1)

output_port_name="/circle/cmd:o"
status_port_name="/circle/status:i"
server_input_port_name="/cnc/cmd:i"
server_status_port_name="/cnc/status:o"

import yarp
yarp.Network.init()
output_port=yarp.BufferedPortBottle()
output_port.open(output_port_name)
status_port=yarp.BufferedPortBottle()
status_port.open(status_port_name)
style=yarp.ContactStyle()
style.persistent=True
yarp.Network.connect(output_port_name, server_input_port_name, style)
yarp.Network.connect(server_status_port_name, status_port_name, style)
#yarp.Time.delay(2)
#while output_port.getOutputCount() <1:
#    print "Waiting for connection to be established getoutputcount"
#    yarp.Time.delay(0.2)
while not yarp.Network.isConnected(output_port_name, server_input_port_name):
    print "Waiting for connection to be established is connected"
    yarp.Time.delay(0.2)
while not yarp.Network.isConnected(server_status_port_name, status_port_name):
    print "Waiting for connection to be established is connected"
    yarp.Time.delay(0.2)

busy=True
while busy:
    print "Waiting for last command to finish"
    output_bottle=output_port.prepare()
    output_bottle.clear()
    output_bottle.addString("status")
    output_port.write()
    output_port.prepare()
    status_bottle=status_port.read(True)
    if status_bottle:
        status=status_bottle.get(0).asInt()
        if status==0:
            busy=False
        else:
            busy=True
    yarp.Time.delay(0.1)
print "Last command finished"

circle0=Circle(motor_step=motor_step, screw_pitch=screw_pitch)
cmds=circle0.do_circle(float(sys.argv[1]), cut_speed=0.003, move_speed=0.05)

print "Cmds: ", cmds
print "Num cmds: ", len(cmds)

for i, cmd in enumerate(cmds):
    print "Current cmd: ", cmd, " cmd progress: ", i, len(cmds), i*100.0/len(cmds), "%"
    if cmd=="up":
        print "Pull drill up"
        raw_input()
        continue
    if cmd=="down":
        print "Pull drill down and adjust drill speed"
        raw_input()
        continue
    busy=True
    while busy:
        #print "Waiting for last command to finish"
        output_bottle=output_port.prepare()
        output_bottle.clear()
        output_bottle.addString("status")
        output_port.write()
        output_port.prepare()
        status_bottle=status_port.read(False)
        if status_bottle:
            status=status_bottle.get(0).asInt()
            if status==0:
                busy=False
            else:
                busy=True
        yarp.Time.delay(0.01)
    #print "Last command finished"
    output_bottle=output_port.prepare()
    output_bottle.clear()
    output_bottle.addString(cmd)
    output_port.write()

output_port.close()
