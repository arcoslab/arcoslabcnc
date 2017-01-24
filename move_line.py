#!/usr/bin/python
#usage: ./move_line.py <x> <y> <z> <speed> <in/mm/m> <abs/rel>
import sys

print sys.argv

if sys.argv[5]=="in":
    system_factor=0.0254
elif sys.argv[5]=="m":
    system_factor=1.0
elif sys.argv[5]=="mm":
    system_factor=0.001
else:
    print "Specify system"
    sys.exit(-1)

speed=float(sys.argv[4])

output_port_name="/move_line/cmd:o"
status_port_name="/move_line/status:i"
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

output_bottle=output_port.prepare()
output_bottle.clear()
if sys.argv[6]=="abs":
    output_bottle.addString("move_abs "+str(system_factor*float(sys.argv[1]))+" "+str(system_factor*float(sys.argv[2]))+" "+str(system_factor*float(sys.argv[3]))+" "+str(speed)) #speed in meters per second
else:
    output_bottle.addString("move "+str(system_factor*float(sys.argv[1]))+" "+str(system_factor*float(sys.argv[2]))+" "+str(system_factor*float(sys.argv[3]))+" "+str(speed)) #speed in meters per second

output_port.write()
output_port.prepare()
while output_port.isWriting():
    print "Still writing"
    yarp.Time.delay(0.1)
output_port.close()
