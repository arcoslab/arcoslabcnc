#!/usr/bin/python
#usage: ./facing.py <xoffset> <yoffset> <zoffset> <xystep> <zstep> <sweep_axis>  <cut_speed> <move_speed> <mm/in/cm>
from math import pi, atan, sin, cos, ceil
from numpy import sign
import sys
motor_step=(0.225, 0.225) #degrees
screw_pitch=(0.005, 0.005) #meters
move_speed=0.005

if sys.argv[9]=="in":
    system_factor=0.0254
elif sys.argv[9]=="m":
    system_factor=1.0
elif sys.argv[9]=="mm":
    system_factor=0.001
else:
    print "Specify system"
    sys.exit(-1)

def frange(x, y, jump):
  while x < y:
    yield x
    x += jump

class Facing:
    def __init__(self, motor_step=(0.9, 0.9), screw_pitch=(0.005, 0.005)):
        self.step_x=motor_step[0]
        self.step_y=motor_step[1]
        self.pitch_x=screw_pitch[0]
        self.pitch_y=screw_pitch[1]
        self.res_x=(self.step_x/360.)*self.pitch_x
        self.res_y=(self.step_y/360.)*self.pitch_y
        self.move_speed=0.005
        self.cut_speed=0.0005

    def do_facing(self, xoffset, yoffset, zoffset, xystep, zstep, speed, move_speed, sweep_axis="x"):
        cmds=[]
        c_depth=0.0
        z_cycles=int(ceil(abs(zoffset)/zstep))+1
        last_cycle_zstep=abs(zoffset)%zstep
        if last_cycle_zstep==0.0:
            last_cycle_zstep=zstep
        print "Cycles: ", z_cycles, " z depth: ", zoffset, " last z step: ", last_cycle_zstep
        c_xyoffset=0.0
        c_zoffset=0.0
        if sweep_axis=="x":
            xy_cycles=int(ceil(abs(yoffset)/xystep))+1
            last_cycle_xystep=abs(yoffset)%xystep
        elif sweep_axis=="y":
            xy_cycles=int(ceil(abs(xoffset)/xystep))+1
            last_cycle_xystep=abs(xoffset)%xystep
        if last_cycle_xystep==0.0:
            last_cycle_xystep=xystep
        print "X Y Cycles: ", xy_cycles, " last xy step: ", last_cycle_xystep
        for i in xrange(z_cycles):
            if i==0:
                c_zoffset=0.0
            elif i==(z_cycles-1):
                c_zoffset=last_cycle_zstep
            else:
                c_zoffset=zstep
            print "Z Level: ", i, " c_zoffset: ", c_zoffset
            cmds.append("move "+str(0.0)+" "+str(0.0)+" "+str(sign(zoffset)*c_zoffset)+" "+str(speed*0.05))
            c_depth+=sign(zoffset)*c_zoffset
            print "Current Z depth: ", c_depth
            for j in xrange(xy_cycles):
                if j==0:
                    c_xyoffset=0.0
                elif j==(xy_cycles-1):
                    c_xyoffset=last_cycle_xystep
                else:
                    c_xyoffset=xystep
                print "XY Level: ", j, " c_xyoffset: ", c_xyoffset
                if sweep_axis=="x":
                    cmds.append("move "+str(0.0)+" "+str(sign(yoffset)*c_xyoffset)+" "+str(0.0)+" "+str(speed*0.5))
                    cmds.append("move "+str(xoffset)+" "+str(0.0)+" "+str(0.0)+" "+str(speed))
                    cmds.append("move "+str(-xoffset)+" "+str(0.0)+" "+str(0.0)+" "+str(move_speed))
                elif sweep_axis=="y":
                    cmds.append("move "+str(sign(xoffset)*c_xyoffset)+" "+str(0.0)+" "+str(0.0)+" "+str(speed*0.5))
                    cmds.append("move "+str(0.0)+" "+str(yoffset)+" "+str(0.0)+" "+str(speed))
                    cmds.append("move "+str(0.0)+" "+str(-yoffset)+" "+str(0.0)+" "+str(move_speed))
            if sweep_axis=="x":
                cmds.append("move "+str(0.0)+" "+str(-yoffset)+" "+str(0.0)+" "+str(move_speed))
            elif sweep_axis=="y":
                cmds.append("move "+str(-xoffset)+" "+str(0.0)+" "+str(0.0)+" "+str(move_speed))

        cmds.append("move "+str(0.0)+" "+str(0.0)+" "+str(-zoffset)+" "+str(speed))
        return(cmds)

print sys.argv

if len(sys.argv)<2:
    sys.exit(-1)

output_port_name="/facing/cmd:o"
status_port_name="/facing/status:i"
server_input_port_name="/cnc/cmd:i"
server_status_port_name="/cnc/status:o"

import yarp
yarp.Network.init()
output_port=yarp.BufferedPortBottle()
output_port.open(output_port_name)
status_port=yarp.BufferedPortBottle()
status_port.open(status_port_name)
status_port.setStrict()
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
    #print "Waiting for last command to finish"
    while status_port.getPendingReads()>0:
        print "Reading old status data"
        status_port.read(True)
    output_bottle=output_port.prepare()
    output_bottle.clear()
    output_bottle.addString("status")
    output_port.writeStrict()
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

facing0=Facing(motor_step=motor_step, screw_pitch=screw_pitch)
cmds=facing0.do_facing(system_factor*float(sys.argv[1]), system_factor*float(sys.argv[2]), system_factor*float(sys.argv[3]), system_factor*float(sys.argv[4]), system_factor*float(sys.argv[5]), float(sys.argv[7]), float(sys.argv[8]), sweep_axis=sys.argv[6])

#print "Cmds: ", cmds
print "Num cmds: ", len(cmds)
old_percentage=0.0
for i, cmd in enumerate(cmds):
    percentage=i*100.0/len(cmds)
    print "Current cmd: ", cmd, " cmd progress: ", i, len(cmds), i*100.0/len(cmds), "%"
    #raw_input()
    if percentage>old_percentage+1.0:
        #print "Current cmd: ", cmd, " cmd progress: ", i, len(cmds), i*100.0/len(cmds), "%"
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
        while status_port.getPendingReads()>0:
            print "Reading old status data"
            status_port.read(True)
        #print "Waiting for last command to finish"
        output_bottle=output_port.prepare()
        output_bottle.clear()
        output_bottle.addString("status")
        output_port.writeStrict()
        output_port.prepare()
        status_bottle=status_port.read(True)
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
    output_port.writeStrict()


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
