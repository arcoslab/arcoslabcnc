#!/usr/bin/python
#usage: ./ring_hole.py <centerx> <centery> <zinit> <zend> <radiusinit> <radiusend> <radiusstep> <zstep> <tooldia> <cut_speed> <move_speed> <angle resolution factor> <in/cm/mm>
from math import pi, atan, sin, cos, ceil
import sys
motor_step=(0.225, 0.225) #degrees
screw_pitch=(0.005, 0.005) #meters
move_speed=0.005

clearance_z=0.005

if sys.argv[13]=="in":
    system_factor=0.0254
elif sys.argv[13]=="m":
    system_factor=1.0
elif sys.argv[13]=="mm":
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

    def do_circle(self, centerx, centery, zinit, zend, radiusinit, radiusend, radiusstep, zstep, tooldia, cut_speed, move_speed, angle_res_factor):
        cmds=[]
        zstep=abs(zstep)
        radiusstep=abs(radiusstep)

        if radiusinit>radiusend:
            print "inward circles"
            radiusinit-=tooldia/2.0
            radiusend+=tooldia/2.0
        else:
            radiusinit+=tooldia/2.0
            radiusend-=tooldia/2.0

        print "Calculating z advancement values"
        zoffset=zend-zinit
        z_cycles=int(ceil(abs(zoffset)/zstep))+1
        last_cycle_zstep=abs(zoffset)%zstep
        if zoffset<0.0:
            zstep=-zstep
            last_cycle_zstep=-last_cycle_zstep
        if last_cycle_zstep==0.0:
            last_cycle_zstep=zstep
        print "Z Cycles: ", z_cycles, " z depth: ", zoffset, " last z step: ", last_cycle_zstep

        c_radius=0.0
        c_z=0.0

        print "Calculating radius advancement values"
        radius_offset=radiusend-radiusinit
        radius_cycles=int(ceil(abs(radius_offset)/radiusstep))+1
        last_cycle_radiusstep=abs(radius_offset)%radiusstep
        if radius_offset<0.0:
            radiusstep=-radiusstep
            last_cycle_radiusstep=-last_cycle_radiusstep
        if last_cycle_radiusstep==0.0:
            last_cycle_radiusstep=radiusstep
        print "Radius Cycles: ", radius_cycles, " last radius step: ", last_cycle_radiusstep

        print "Moving up 10mm"
        cmds.append("move "+str(0.0)+" "+str(0.0)+" "+str(0.010)+" "+str(move_speed))
        print "Moving to circle start point 10mm up"
        cmds.append("move_abs "+str(centerx+radiusinit)+" "+str(centery)+" "+str(0.010)+" "+str(move_speed))

        for i in xrange(z_cycles):
            if i==0:
                c_z=zinit
            elif i==(z_cycles-1):
                c_z+=last_cycle_zstep
            else:
                c_z+=zstep
            print "Z Level: ", i, " current z: ", c_z
            cmds.append("pause")
            for j in xrange(radius_cycles):
                if j==0:
                    c_radius=radiusinit
                elif j==(radius_cycles-1):
                    c_radius+=last_cycle_radiusstep
                else:
                    c_radius+=radiusstep
                print "Radius Level: ", j, " c_radius: ", c_radius

                if radiusstep<0.0:
                    print "Moving from outside to inside. Selecting ccw movement"
                    move="move_abs_arc_ccw "
                    move="move_abs_arc_cw "
                else:
                    move="move_abs_arc_cw "
                    move="move_abs_arc_ccw "
                if j==0:
                    print "First slot, going in with less DOC"
                    cuts=1
                    if move=="move_abs_arc_ccw ":
                        move="move_abs_arc_cw "
                    else:
                        move="move_abs_arc_ccw "
                else:
                    cuts=1
                for k in xrange(cuts):
                    cmds.append("move_abs "+str(centerx+c_radius)+" "+str(centery)+" "+str(zinit+abs(zstep)+0.010)+" "+str(move_speed))
                    cmds.append("move_abs "+str(centerx+c_radius)+" "+str(centery)+" "+str(zinit+abs(zstep)+0.001)+" "+str(move_speed))
                    cmds.append("move_abs "+str(centerx+c_radius)+" "+str(centery)+" "+str(c_z-(zstep/cuts)*(cuts-1-k))+" "+str(0.1*cut_speed))
                    cmds.append(move+str(centerx-c_radius)+" "+str(centery)+" "+str(c_z-(zstep/cuts)*(cuts-1-k))+" "+str(-c_radius)+" "+str(0.0)+" "+str(cut_speed)+" "+str(angle_res_factor))
                    cmds.append(move+str(centerx+c_radius)+" "+str(centery)+" "+str(c_z-(zstep/cuts)*(cuts-1-k))+" "+str(c_radius)+" "+str(0.0)+" "+str(cut_speed)+" "+str(angle_res_factor))
                    cmds.append("move_abs "+str(centerx+c_radius)+" "+str(centery)+" "+str(zinit+abs(zstep)+0.010)+" "+str(move_speed))

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

circle0=Circle(motor_step=motor_step, screw_pitch=screw_pitch)
cmds=circle0.do_circle(system_factor*float(sys.argv[1]), system_factor*float(sys.argv[2]), system_factor*float(sys.argv[3]), system_factor*float(sys.argv[4]), system_factor*float(sys.argv[5]), system_factor*float(sys.argv[6]), system_factor*float(sys.argv[7]), system_factor*float(sys.argv[8]), system_factor*float(sys.argv[9]), float(sys.argv[10]), float(sys.argv[11]), float(sys.argv[12]))

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
