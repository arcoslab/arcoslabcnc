#!/usr/bin/python
#usage: ./filet.py <centerx> <centery> <radiusinit> <zinit> <zend> <angle_fillet_cycles> <tooldia> <cut_speed> <move_speed> <angle resolution factor> <outside> <in/cm/mm>
from math import pi, asin, sin, cos, ceil
import sys

if sys.argv[12]=="in":
    system_factor=0.0254
elif sys.argv[12]=="m":
    system_factor=1.0
elif sys.argv[12]=="mm":
    system_factor=0.001
else:
    print "Specify system"
    sys.exit(-1)

def frange(x, y, jump):
  while x < y:
    yield x
    x += jump

def get_fillet_xystep(fillet_z, fillet_radius):
    angle=asin(fillet_z/fillet_radius)
    print "Current fillet angle: ", angle*180.0/pi
    fillet_y=fillet_radius*cos(angle)
    print "Current fillet z: ", fillet_z, ", y: ", fillet_y
    return(fillet_y)

def get_fillet_xyzstep(angle, fillet_radius):
    print "Current fillet angle: ", angle*180.0/pi
    fillet_y=fillet_radius*cos(angle)
    fillet_z=fillet_radius*sin(angle)
    print "Current fillet z: ", fillet_z, ", y: ", fillet_y
    return(fillet_y, fillet_z)

class Fillet:
    def __init__(self):
        pass

    def do_fillet(self, centerx, centery, radiusinit, zinit, zend, angle_fillet_cycles, tooldia, cut_speed, move_speed, angle_res_factor, outside):
        cmds=[]
        #zstep=abs(zstep)
        if outside=="outside":
            radiusinit+=tooldia/2.0
        elif outside=="inside":
            radiusinit-=tooldia/2.0
        else:
            print "Error, no inside outside"
            exit()

        fillet_radius=abs(zend-zinit)

        print "Fillet radius: ", fillet_radius

        print "Calculating z advancement values"
        zoffset=zend-zinit
        # z_cycles=int(ceil(abs(zoffset)/zstep))+1
        # last_cycle_zstep=abs(zoffset)%zstep
        # if zoffset<0.0:
        #     zstep=-zstep
        #     last_cycle_zstep=-last_cycle_zstep
        # if last_cycle_zstep==0.0:
        #     last_cycle_zstep=zstep
        # print "Z Cycles: ", z_cycles, " z depth: ", zoffset, " last z step: ", last_cycle_zstep

        c_radius=radiusinit
        c_z=zinit

        # print "Calculating radius advancement values"
        # radius_offset=radiusend-radiusinit
        # radius_cycles=int(ceil(abs(radius_offset)/radiusstep))+1
        # last_cycle_radiusstep=abs(radius_offset)%radiusstep
        # if radius_offset<0.0:
        #     radiusstep=-radiusstep
        #     last_cycle_radiusstep=-last_cycle_radiusstep
        # if last_cycle_radiusstep==0.0:
        #     last_cycle_radiusstep=radiusstep
        # print "Radius Cycles: ", radius_cycles, " last radius step: ", last_cycle_radiusstep

        print "Moving up 10mm"
        cmds.append("move "+str(0.0)+" "+str(0.0)+" "+str(0.010)+" "+str(move_speed))
        print "Moving to circle start point 10mm up"
        cmds.append("move_abs "+str(centerx+radiusinit)+" "+str(centery)+" "+str(zinit+abs(zoffset)+0.0100)+" "+str(move_speed))

        c_radius=radiusinit
        #cycles=z_cycles
        #cycles=300 # 100 angles
        cycles=angle_fillet_cycles
        print "Angles selected: ", cycles

        for i in xrange(cycles):
            old_z=c_z
            print "Z Level: ", i, " current z: ", c_z
            #cmds.append("pause")
            #fillet_z=c_z-zinit
            #c_radius=radiusinit+fillet_radius-get_fillet_xystep(fillet_z, fillet_radius)
            angle=(90.0*pi/180.0)*i/cycles
            fillet_y, fillet_z=get_fillet_xyzstep(angle, fillet_radius)
            if outside=="outside":
                c_radius=radiusinit+fillet_radius-fillet_y
            elif outside=="inside":
                c_radius=radiusinit-fillet_radius+fillet_y
            else:
                print "Error, no inside or outside"
                exit()
            c_z=zinit-fillet_z
            cmds.append("move_abs "+str(centerx+c_radius)+" "+str(centery)+" "+str(old_z)+" "+str(move_speed))
            cmds.append("move_abs "+str(centerx+c_radius)+" "+str(centery)+" "+str(c_z)+" "+str(0.1*cut_speed))
            move="move_abs_arc_cw "
            cmds.append(move+str(centerx-c_radius)+" "+str(centery)+" "+str(c_z)+" "+str(-c_radius)+" "+str(0.0)+" "+str(cut_speed)+" "+str(angle_res_factor))
            cmds.append(move+str(centerx+c_radius)+" "+str(centery)+" "+str(c_z)+" "+str(c_radius)+" "+str(0.0)+" "+str(cut_speed)+" "+str(angle_res_factor))

        print "Moving up 10mm"
        cmds.append("move "+str(0.0)+" "+str(0.0)+" "+str(abs(zoffset)+0.010)+" "+str(move_speed))
        #print "Moving 0 0 10mm"
        #cmds.append("move_abs "+str(0.0)+" "+str(0.0)+" "+str(zinit+0.010)+" "+str(move_speed))
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

fillet0=Fillet()
cmds=fillet0.do_fillet(system_factor*float(sys.argv[1]), system_factor*float(sys.argv[2]), system_factor*float(sys.argv[3]), system_factor*float(sys.argv[4]), system_factor*float(sys.argv[5]), int(sys.argv[6]), system_factor*float(sys.argv[7]), float(sys.argv[8]), float(sys.argv[9]), float(sys.argv[10]), sys.argv[11])

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
    if cmd=="pause":
        print "Waiting"
        raw_input()
        continue
    if cmd=="down":
        print "Pull drill down and adjust drill speed"
        #raw_input()
        continue
    busy=True
    while busy:
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
