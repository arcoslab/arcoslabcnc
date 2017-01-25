#!/usr/bin/python
#usage: ./gcode_exec.py <gcode_file> <cut_speed> <fast_speed>
import sys
from time import sleep
import re

from time import time as time_now
print sys.argv

start_t=time_now()

output_port_name="/gcode/cmd:o"
status_port_name="/gcode/status:i"
server_input_port_name="/cnc/cmd:i"
server_status_port_name="/cnc/status:o"
cut_speed=float(sys.argv[2])
fast_speed=float(sys.argv[3])

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

for i, line in enumerate(lines):
    print
    print "Line: ", line[:-1], " i: ", i, " of ", len(lines), " lines ", i*100.0/len(lines), "%"
    line=line.strip()
    if line[0]==";":
        print "Comment line, ignoring"
        continue
    cmds=line.split(" ")
    exec_motion=False
    prev_cmd=""
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
        elif cmd=="G04":
            print "Wait"
            prev_cmd="G04"
        elif cmd[0]=="P":
            if prev_cmd=="G04":
                cmd_tmp=re.split('(\d+\.*\d*)', cmd)
                value=float(cmd_tmp[1])
                print "Waiting for: ", value, " seconds"
                sleep(value)
        elif cmd=="G1":
            print "Linear move"
            movement_type="linear"
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
            z=float(cmd_tmp[1])
            print "Z: ", z
            exec_motion=True
        else:
            print "Cmd unknown"
            raw_input()
    if exec_motion:
        if movement_type=="rapid":
            speed=fast_speed
        elif movement_type=="linear":
            speed=cut_speed
        else:
            speed=cut_speed
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
            yarp.Time.delay(0.1)
        print "Last command finished"
        output_bottle=output_port.prepare()
        output_bottle.clear()
        if rel:
            output_bottle.addString("move "+str(system_factor*x)+" "+str(system_factor*y)+" "+str(system_factor*z)+" "+str(speed)) #speed in meters per second
        else:
            output_bottle.addString("move_abs "+str(system_factor*x)+" "+str(system_factor*y)+" "+str(system_factor*z)+" "+str(speed)) #speed in meters per second
        output_port.writeStrict()
        while output_port.isWriting():
            print "Still writing"
            yarp.Time.delay(0.1)

output_port.close()

end_t=time_now()
print "Print job took: ", end_t-start_t, " seconds to complete"
