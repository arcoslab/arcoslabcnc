#!/usr/bin/python
#usage: ./circle.py <centerx> <centery> <centerz> <radius> <turns> <cut_speed> <angle resolution factor> <in/cm>
from math import pi, atan, sin, cos
import sys
motor_step=(0.225, 0.225) #degrees
screw_pitch=(0.005, 0.005) #meters
move_speed=0.005

if sys.argv[8]=="in":
    system_factor=0.0254
elif sys.argv[8]=="m":
    system_factor=1.0
elif sys.argv[8]=="mm":
    system_factor=0.001
else:
    print "Specify system"
    sys.exit(-1)

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
        self.move_speed=0.005
        self.cut_speed=0.0005

    def do_circle(self, centerx, centery, centerz, radius, cut_speed=0.03, move_speed=0.05, turns=1, angle_res_factor=1.0):
        cmds=[]
        step_angle=angle_res_factor*atan(self.res_x/radius)*360.0/(2.*pi)
        print "Step angle: ", step_angle
        old_x=0.0
        old_y=0.0
        iteration=0
        print "Positioning piece in circle center"
        cmds.append("up")
        speed=cut_speed
        #cmds.append("move_abs "+str(centerx)+" "+str(centery)+" "+str(speed))
        for i in xrange(turns):
            for angle in frange(0., 360.0, step_angle):
                x=radius*cos(angle*(2*pi)/360.0)
                y=radius*sin(angle*(2*pi)/360.0)
                if iteration==0:
                    print "Moving to first circle position, pull bit up!"
                    cmds.append("up")
                    iteration=1
                    speed=cut_speed
                elif iteration==1:
                    print "Start mill position, pull bit down at desired height!"
                    cmds.append("down")
                    iteration=2
                    speed=cut_speed

                #print "Angle: ", angle, "X, Y: ", x, y, x-old_x, y-old_y
                #raw_input()
                #cmds.append("move "+str(x-old_x)+" "+str(y-old_y)+" "+str(speed))
                cmds.append("move_abs "+str(x+centerx)+" "+str(y+centery)+" "+str(centerz)+" "+str(speed))
                old_x=x
                old_y=y
            #cmds.append("down")
        print "Pull bit up!, moving fast to center"
        cmds.append("up")
        speed=move_speed
        #cmds.append("move "+str(-radius)+" "+str(0.0)+" "+str(speed))
        #cmds.append("move_abs "+str(centerx)+" "+str(centery)+" "+str(speed))
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
cmds=circle0.do_circle(system_factor*float(sys.argv[1]), system_factor*float(sys.argv[2]), system_factor*float(sys.argv[3]), system_factor*float(sys.argv[4]), cut_speed=float(sys.argv[6]), move_speed=move_speed, turns=int(sys.argv[5]), angle_res_factor=float(sys.argv[7]))

#print "Cmds: ", cmds
print "Num cmds: ", len(cmds)
old_percentage=0.0
for i, cmd in enumerate(cmds):
    percentage=i*100.0/len(cmds)
    if percentage>old_percentage+1.0:
        print "Current cmd: ", cmd, " cmd progress: ", i, len(cmds), i*100.0/len(cmds), "%"
        old_percentage=percentage
    if cmd=="up":
        print "Pull drill up"
        #raw_input()
        continue
    if cmd=="down":
        print "Pull drill down and adjust drill speed"
        #raw_input()
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
output_port.close()
