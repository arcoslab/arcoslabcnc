#!/usr/bin/python

import sys

print sys.argv

if len(sys.argv)<4:
    speed=0.002
else:
    speed=float(sys.argv[3])

output_port_name="/move_line/cmd:o"
server_input_port_name="/cnc/cmd:i"

import yarp
yarp.Network.init()
output_port=yarp.BufferedPortBottle()
output_port.open(output_port_name)
style=yarp.ContactStyle()
style.persistent=True
yarp.Network.connect(output_port_name, server_input_port_name, style)
#yarp.Time.delay(2)
#while output_port.getOutputCount() <1:
#    print "Waiting for connection to be established getoutputcount"
#    yarp.Time.delay(0.2)
while not yarp.Network.isConnected(output_port_name, server_input_port_name):
    print "Waiting for connection to be established is connected"
    yarp.Time.delay(0.2)

output_bottle=output_port.prepare()
output_bottle.clear()
output_bottle.addString("move "+sys.argv[1]+" "+sys.argv[2]+" "+str(speed)) #speed in meters per second
output_port.write()
output_port.prepare()
while output_port.isWriting():
    print "Still writing"
    yarp.Time.delay(0.1)
output_port.close()
