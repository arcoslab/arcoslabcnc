#!/usr/bin/python
#usage: ./park
import sys

print sys.argv

output_port_name="/park/cmd:o"
status_port_name="/park/status:i"
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
    while status_port.getPendingReads()>0:
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

speed=0.008
x=0.0000
y=0.0000
z=0.020

output_bottle=output_port.prepare()
output_bottle.clear()
output_bottle.addString("move "+str(x)+" "+str(y)+" "+str(z)+" "+str(speed)) #speed in meters per second
output_port.writeStrict()
output_port.prepare()
while output_port.isWriting():
    print "Still writing"
    yarp.Time.delay(0.1)

busy=True
while busy:
    print "Waiting for last command to finish"
    while status_port.getPendingReads()>0:
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


speed=0.008
x=0.0000
y=0.0000
z=0.020

output_bottle=output_port.prepare()
output_bottle.clear()
output_bottle.addString("move_abs "+str(x)+" "+str(y)+" "+str(z)+" "+str(speed)) #speed in meters per second
output_port.writeStrict()
output_port.prepare()
while output_port.isWriting():
    print "Still writing"
    yarp.Time.delay(0.1)

busy=True
while busy:
    print "Waiting for last command to finish"
    while status_port.getPendingReads()>0:
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


speed=0.008
x=0.0000
y=0.0000
z=0.001

output_bottle=output_port.prepare()
output_bottle.clear()
output_bottle.addString("move_abs "+str(x)+" "+str(y)+" "+str(z)+" "+str(speed)) #speed in meters per second
output_port.writeStrict()
output_port.prepare()
while output_port.isWriting():
    print "Still writing"
    yarp.Time.delay(0.1)

busy=True
while busy:
    print "Waiting for last command to finish"
    while status_port.getPendingReads()>0:
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

speed=0.0005
x=-0.00001
y=-0.00001
z=-0.00001

output_bottle=output_port.prepare()
output_bottle.clear()
output_bottle.addString("move_abs "+str(x)+" "+str(y)+" "+str(z)+" "+str(speed)) #speed in meters per second
output_port.writeStrict()
output_port.prepare()
while output_port.isWriting():
    print "Still writing"
    yarp.Time.delay(0.1)

busy=True
while busy:
    print "Waiting for last command to finish"
    while status_port.getPendingReads()>0:
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

speed=0.0005
x=0.0
y=0.0
z=0.0

output_bottle=output_port.prepare()
output_bottle.clear()
output_bottle.addString("move_abs "+str(x)+" "+str(y)+" "+str(z)+" "+str(speed)) #speed in meters per second
output_port.writeStrict()
output_port.prepare()
while output_port.isWriting():
    print "Still writing"
    yarp.Time.delay(0.1)

output_port.close()
