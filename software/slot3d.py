#!/usr/bin/python
#usage: ./slot3d.py <x1> <y1> <x2> <y2> <zinit> <zend> <zstep> <cut_speed> <mm/in/cm>
from math import pi, atan, sin, cos
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

class Slot3d:
    def __init__(self, motor_step=(0.9, 0.9), screw_pitch=(0.005, 0.005)):
        self.step_x=motor_step[0]
        self.step_y=motor_step[1]
        self.pitch_x=screw_pitch[0]
        self.pitch_y=screw_pitch[1]
        self.res_x=(self.step_x/360.)*self.pitch_x
        self.res_y=(self.step_y/360.)*self.pitch_y
        self.move_speed=0.005
        self.cut_speed=0.0005

    def do_slot(self, x1, y1, x2, y2, zinit, zend, zstep, speed):
        cmds=[]
        z_depth=zend-zinit
        cycles=abs(int((z_depth/zstep)))+2
        print "Cycles: ", cycles, " z_depth: ", z_depth
        #step_angle=angle_res_factor*atan(self.res_x/radius)*360.0/(2.*pi)
        #print "Step angle: ", step_angle, " centerzinit, centerzend: ", centerzinit, centerzend
        #z_int_step=zstep/(360.0/step_angle) # z movement for each x,y move command
        if (zend-zinit)<0.0:
            zstep=-zstep
        #turns=int(abs((centerzend-centerzinit))/zstep)+3
        #print "Step angle: ", step_angle, " z int step: ", z_int_step, " turns: ", turns
        raw_input()
        z=0.0
        for i in xrange(int(cycles)):
            print "Z: ", z, " Zinit+z: ", zinit+z
            cmds.append("move_abs "+str(x1)+" "+str(y1)+" "+str(zinit+z)+" "+str(speed))
            z+=zstep/2.0
            if zstep>=0.0:
                if zinit+z>zend:
                    z=zend-zinit
            else:
                if zinit+z<zend:
                    z=zend-zinit
            cmds.append("move_abs "+str(x2)+" "+str(y2)+" "+str(zinit+z)+" "+str(speed))
            z+=zstep/2.0
            if zstep>=0.0:
                if zinit+z>zend:
                    z=zend-zinit
                    print "Bottom reached. Holding z position."
            else:
                if zinit+z<zend:
                    z=zend-zinit
                    print "Bottom reached. Holding z position."
        cmds.append("move_abs "+str(x1)+" "+str(y1)+" "+str(zinit+z)+" "+str(speed))
        return(cmds)

print sys.argv

if len(sys.argv)<2:
    sys.exit(-1)

output_port_name="/slot3d/cmd:o"
status_port_name="/slot3d/status:i"
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

slot0=Slot3d(motor_step=motor_step, screw_pitch=screw_pitch)
cmds=slot0.do_slot(system_factor*float(sys.argv[1]), system_factor*float(sys.argv[2]), system_factor*float(sys.argv[3]), system_factor*float(sys.argv[4]), system_factor*float(sys.argv[5]), system_factor*float(sys.argv[6]), system_factor*float(sys.argv[7]), float(sys.argv[8]))

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
