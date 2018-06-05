#!/usr/bin/python
#usage: ./gcode_exec.py <gcode_file> <cut_speed> <fast_speed> <start_line> <angle_res_factor>
import sys
from time import sleep
import re

from time import time as time_now
print sys.argv

start_t=time_now()

start_line=int(sys.argv[4])

print "Start line: ", start_line
raw_input()

output_port_name="/gcode/cmd:o"
status_port_name="/gcode/status:i"
server_input_port_name="/cnc/cmd:i"
server_status_port_name="/cnc/status:o"
cut_speed=float(sys.argv[2])
fast_speed=float(sys.argv[3])
angle_res_factor=float(sys.argv[5])

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

gcode_h=open(sys.argv[1])
rel=True
system="mm"
movement_type="linear"
x=0.0
y=0.0
z=0.0
exec_motion=False

print "Resetting position to 0 to current position"
output_bottle=output_port.prepare()
output_bottle.clear()
output_bottle.addString("reset_pos")
output_port.writeStrict()
sleep(1)

system_factor=0.001

lines=gcode_h.readlines()

jump_to_future=False

temp_start_line=0
for i, line in enumerate(lines):
    print "Line: ", line[:-1], " i: ", i, " of ", len(lines), " lines ", i*100.0/len(lines), "%"
    if i==start_line:
        print "finished search"
        break
    line=line.strip()
    if line[0]==";":
        print "Comment line, ignoring"
        continue
    cmds=line.split(" ")
    has_g0=False
    has_x=False
    has_y=False
    for cmd in cmds:
        print cmd
        if cmd=="G0":
            has_g0=True
        if cmd[0]=="X":
            has_x=True
        if cmd[0]=="Y":
            has_y=True
    if has_x and has_y and has_g0:
        print "Has x y and g0!!", i
        temp_start_line=i
print "Last X and Y in G0 movement before start line in: ", temp_start_line
raw_input()
z=5.0
start_line=temp_start_line

for i, line in enumerate(lines):
    print
    print "Line: ", line[:-1], " i: ", i, " of ", len(lines), " lines ", i*100.0/len(lines), "%"
    if jump_to_future:
        if i<start_line:
            print "Skipping line"
            continue
    line=line.strip()
    if line[0]==";":
        print "Comment line, ignoring"
        continue
    cmds=line.split(" ")
    exec_motion=False
    prev_cmd=""
    z_down_in=False
    spindle_speed=0.0
    for cmd in cmds:
        print "Interpreting cmd: ", cmd
        if (cmd[0]==";") or (cmd[0]=="("):
            print "Comment starts, ignoring the rest"
            break
        elif cmd=="G40":
            print "Ignore"
        elif cmd=="G49":
            print "Ignore"
        elif cmd=="G80":
            print "Ignore"
        elif cmd=="G54":
            print "Ignore"
        elif cmd=="G90":
            print "Using absolute values"
            rel=False
        elif cmd=="G21":
            print "Metric system selected"
            system="mm"
            if system=="in":
                system_factor=0.0254
            elif system=="m":
                system_factor=1.0
            elif system=="mm":
                system_factor=0.001

        elif cmd=="G61":
            print "Exact Path mode. Ignoring for now (should not stop at each point, smooth movement"
        elif cmd[0]=="F":
            feed_cmd=re.split('(\d+\.*\d*)', cmd)
            feed_rate=float(feed_cmd[1])
            print "Feedrate: ", feed_rate, " Ignoring for now"
        elif cmd[0]=="S":
            spindle_cmd=re.split('(\d+\.*\d*)', cmd)
            spindle_speed=float(spindle_cmd[1])
            print "Spidle speed: ", spindle_speed
            raw_input()
        elif cmd[0]=="T":
            cmd_tmp=re.split('(\d+\.*\d*)', cmd)
            value=float(cmd_tmp[1])
            print "Select tool: ", value
        elif cmd=="M6":
            print "Change tool now!"
            raw_input()
        elif cmd=="M3":
            print "Start spindle to ", spindle_speed, " now!"
            raw_input()
        elif cmd=="M5":
            print "Stop spindle"
            raw_input()
        elif cmd=="M2":
            print "The End!"
            raw_input()
        elif cmd=="G0":
            print "Rapid move"
            movement_type="rapid"
            if start_line>0:
                print "First G0 movement. Machine configured"
                jump_to_future=True
        elif cmd=="G04":
            print "Wait"
            prev_cmd="G04"
        elif cmd[0]=="P":
            if prev_cmd=="G04":
                cmd_tmp=re.split('(\d+\.*\d*)', cmd)
                value=float(cmd_tmp[1])
                print "Waiting for: ", value, " seconds"
                sleep(value)
                if start_line>0:
                    print "Starting ahead!"
                    jump_to_future=True
        elif cmd=="G1":
            print "Linear move"
            movement_type="linear"
        elif cmd=="G2":
            print "Arc move CW"
            movement_type="arc_cw"
        elif cmd=="G3":
            print "Arc move CCW"
            movement_type="arc_ccw"
        elif cmd[0]=="X":
            cmd_tmp=re.split('(-*\d+\.*\d*)', cmd)
            x=float(cmd_tmp[1])
            print "X: ", x
            exec_motion=True
        elif cmd[0]=="Y":
            cmd_tmp=re.split('(-*\d+\.*\d*)', cmd)
            y=float(cmd_tmp[1])
            print "Y: ", y
            exec_motion=True
        elif cmd[0]=="Z":
            cmd_tmp=re.split('(-*\d+\.*\d*)', cmd)
            z_old=z
            z=float(cmd_tmp[1])
            print "Z: ", z
            exec_motion=True
            if z<z_old:
                print "Moving down"
                if z<=0.0:
                    print "Moving inside"
                    z_down_in=True
        elif cmd[0]=="I":
            cmd_tmp=re.split('(-*\d+\.*\d*)', cmd)
            i_arc=float(cmd_tmp[1])
            print "I: ", i_arc
            exec_motion=True
        elif cmd[0]=="J":
            cmd_tmp=re.split('(-*\d+\.*\d*)', cmd)
            j_arc=float(cmd_tmp[1])
            print "J: ", j_arc
            exec_motion=True
        else:
            print "Cmd unknown"
            raw_input()
    if exec_motion:
        if (movement_type=="arc_cw") or (movement_type=="arc_ccw"):
            speed=cut_speed
        elif movement_type=="rapid":
            speed=fast_speed
        elif movement_type=="linear":
            speed=cut_speed
        else:
            speed=cut_speed
        if z_down_in and movement_type!="arc_cw" and movement_type!="arc_ccw":
            print "Moving in z cutting, even slower"
            z_scale=0.25
        else:
            z_scale=1.0
        speed*=z_scale
        print "Moving to: ", x, y, z, " speed: ", speed
        #raw_input()
        busy=True
        while busy:
            #print "Waiting for last command to finish"
            while status_port.getPendingReads()>0:
                #print "Reading old status data"
                status_port.read(True)
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
            yarp.Time.delay(0.001)
        print "Last command finished"
        output_bottle=output_port.prepare()
        output_bottle.clear()
        if z_down_in:
            if system_factor*z_old>0.1:
                print "Starts above 0.1 z, then we split the movement"
                if rel:
                    output_bottle.addString("move "+str(system_factor*x)+" "+str(system_factor*y)+" "+str(0.1)+" "+str(fast_speed)) #speed in meters per second
                else:
                    output_bottle.addString("move_abs "+str(system_factor*x)+" "+str(system_factor*y)+" "+str(0.1)+" "+str(fast_speed)) #speed in meters per second
        if movement_type=="arc_cw":
            print "ARC_CW"
            output_bottle.addString("move_abs_arc_cw "+str(system_factor*x)+" "+str(system_factor*y)+" "+str(system_factor*z)+" "+str(system_factor*i_arc)+" "+str(system_factor*j_arc)+" "+str(speed)+" "+str(angle_res_factor)) #speed in meters per second
        elif movement_type=="arc_ccw":
            print "ARC_CCW"
            output_bottle.addString("move_abs_arc_ccw "+str(system_factor*x)+" "+str(system_factor*y)+" "+str(system_factor*z)+" "+str(system_factor*i_arc)+" "+str(system_factor*j_arc)+" "+str(speed)+" "+str(angle_res_factor)) #speed in meters per second
        else:
            if rel:
                output_bottle.addString("move "+str(system_factor*x)+" "+str(system_factor*y)+" "+str(system_factor*z)+" "+str(speed)) #speed in meters per second
            else:
                output_bottle.addString("move_abs "+str(system_factor*x)+" "+str(system_factor*y)+" "+str(system_factor*z)+" "+str(speed)) #speed in meters per second
        output_port.writeStrict()
        while output_port.isWriting():
            print "Still writing"
            yarp.Time.delay(0.001)

output_port.close()

end_t=time_now()
print "Print job took: ", end_t-start_t, " seconds to complete"
