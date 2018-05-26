#!/usr/bin/python
#usage: ./kbd_speed.py <step percent>
import sys

print sys.argv
from arcospyu.rawkey import Raw_key,Keys, is_key

step_percent=float(sys.argv[1])
print "Step percent: ", step_percent

output_port_name="/kbd_speed/cmd:o"
status_port_name="/kbd_speed/status:i"
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


speed_scale=1.0

raw_key=Raw_key()

while True:
    num_chars=raw_key.get_num_chars(None)
    print "got", num_chars
    if is_key(num_chars,Keys.UP_ARROW):
        print "UP!"
        up=True
    else:
        up=False
    if is_key(num_chars,Keys.DOWN_ARROW):
        print "Down!"
        down=True
    else:
        down=False
    if is_key(num_chars,Keys.q):
        break
    if up:
        speed_scale*=1.0+step_percent*0.01
    if down:
        speed_scale*=1.0-step_percent*0.01
    print "Sending: ", speed_scale
    output_bottle=output_port.prepare()
    output_bottle.clear()
    output_bottle.addString("speed_scale "+str(speed_scale))
    output_port.writeStrict()
    output_port.prepare()
    while output_port.isWriting():
        print "Still writing"
        yarp.Time.delay(0.1)
output_port.close()
