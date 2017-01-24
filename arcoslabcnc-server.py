#!/usr/bin/python

from gpiozero import DigitalOutputDevice as dig
from gpiozero import DigitalOutputDevice as pwm
from time import sleep
import time
from multiprocessing import Process, Queue
input_port_name="/cnc/cmd:i"
status_port_name="/cnc/status:o"
pos_port_name="/cnc/pos:o"


class Axis:
    def __init__(self, stepper, pitch=0.005):
        #pitch = meters per revolution
        self.pitch=pitch
        self.stepper=stepper

    def disable(self):
        self.stepper.disable()

    def enable(self):
        self.stepper.enable()

    def is_moving(self):
        return(self.stepper.is_moving())

    def move(self, distance, speed=0.001):
        #distance in meters!
        #speed in meters/second
        if speed<0.0:
          speed=-speed
          distance=-distance
        if speed==0.0:
          distance=0.0
          speed=0.001
        #print "Moving: ", distance/self.pitch, " revolutions"
        self.stepper.move_angle(360.0*distance/self.pitch, speed/self.pitch)

    def move_abs(self, pos, speed=0.001):
        self.move(pos-self.cur_pos, speed)

    def update(self):
        self.cur_pos=(self.stepper.cur_angle/360.0)*self.pitch

class PreciseSpeed:
  def __init__(self, pin):
    self.queue=Queue()
    self.process=Process(target=self.loop, args=(pin, self.queue,))
    self.process.start()

  def loop(self, pin, queue):
    print "Starting loop"
    self.dev=pwm(pin, active_high=False)
    steps,freq=(0,0)
    print "First loop data: ", steps, freq
    while True:
      print "*******Looping!!!  Steps: ", steps, " Queue size: ", queue.qsize()
      try:
        while not queue.empty():
          steps,freq=queue.get(False)
          print "*****Loop: New steps and freq: ", steps, freq
      except:
        pass
        #print "No data in queue"
      if steps>0:
        print "*********Loop: Step1: ", steps
        steps-=1
        self.dev.on()
        sleep((1.0/freq)/2.0)
        self.dev.off()
        sleep((1.0/freq)/2.0)
        print "*********Loop: Step2: ", steps
      else:
        #print "No steps, motor off"
        self.dev.off()
      sleep(0.01)

  def move_steps(self, steps, freq=1.0):
    self.queue.put((steps, freq))

class Stepper:
    def __init__(self, pulse_pin, dir_pin, ena_pin, step=0.9, period=0.002):
        #step in degrees
        self.pulse_pin=pulse_pin
        self.dir_pin=dir_pin
        self.ena_pin=ena_pin
        self.step=step
        self.pulse=pwm(self.pulse_pin, active_high=False)
        #self.precisespeed=PreciseSpeed(pulse_pin)
        #self.pulse.value=0.5
        self.direction=dig(self.dir_pin, active_high=False)
        self.ena=dig(self.ena_pin, active_high=True)
        self.on_time=period/2.
        self.off_time=self.on_time
        self.dir_wait=self.on_time
        self.step_rest=0.0
        self.period=0.0
        self.disable()
        self.time=time.time()
        self.time_last_toggle=self.time
        self.state=False
        self.steps=0
        self.cur_angle=0.0
        self.cur_steps=0
        self.cur_dir=False

    def reset_pos(self):
        self.cur_angle=0.0
        self.cur_steps=0
        self.step_rest=0.0

    def enable(self):
        self._enable=True
        self.ena.on()

    def is_moving(self):
        return(self.pulse._blink_thread.isAlive())

    def disable(self):
        self._enable=False
        self.ena.off()
        self.direction.off()
        #self.pulse.off()

    def stop(self):
        self.disable()
        self.steps=0
        self.step_rest=0.0

    def move_angle(self, delta_angle, rps):
        #angle in degrees
        #rps rev per second
        #print "Moving: ", delta_angle/self.step, " steps"
        total_steps=self.step_rest+delta_angle/self.step
        step_rest=total_steps-float(int(total_steps))
        #print "Total steps: ", total_steps, " step rest: ", step_rest
        if abs(step_rest)>=0.5:
            #print "Stepping one more!"
            if step_rest>0:
                steps=int(total_steps)+1
            else:
                steps=int(total_steps)-1
        else:
            #print "Stepping truncated"
            steps=int(total_steps)
        self.step_rest=total_steps-steps
        #print "Step rest: ", self.step_rest
        self.move_steps(steps, rps*360.0/self.step)

    def move_steps(self, steps, speed):
        #speed in steps per second
        self.period=1.0/speed
        self.steps=abs(steps)
        #print "Steps: ", steps, " Speed: ", speed, " period: ", self.period
        if self._enable:
            if steps<0:
            #    print "Pos dir"
                self.direction.on()
                self.cur_dir=True
            else:
            #    print "Neg dir"
                self.direction.off()
                self.cur_dir=False
            #sleep(self.dir_wait)
            #print "Pulsing"
            #self.pulse.blink(on_time=period/2.0, off_time=period/2.0, n=abs(steps), background=True)
            #self.toggle(n=abs(steps))
            #self.precisespeed.move_steps(abs(steps), speed)
            #print "Finished pulsing"

    def update(self):
      #print "Updating motor"
      if self._enable:
        new_time=time.time()
        if self.period==0.0:
          self.pulse.off()
        else:
          if (new_time-self.time_last_toggle)>=self.period:
            #print "*****Time to toggle! ", new_time-self.time_last_toggle
            self.time_last_toggle+=self.period
            if self.steps>0:
              if self.state:
                self.pulse.off()
                self.state=False
                self.steps-=1
              else:
                self.pulse.on()
                self.state=True
                if self.cur_dir:
                  self.cur_steps-=1
                else:
                  self.cur_steps+=1
                self.cur_angle=self.cur_steps*self.step

    def isBusy(self):
      if self.steps==0:
        return(False)
      else:
        return(True)

    def toggle(self, n=1):
        for i in xrange(n):
            self.pulse.on()
            sleep(self.on_time)
            self.pulse.off()
            sleep(self.on_time)

    def __del__(self):
        self.disable()


if __name__=="__main__":
  import yarp
  yarp.Network.init()
  input_port=yarp.BufferedPortBottle()
  input_port.open(input_port_name)
  status_port=yarp.BufferedPortBottle()
  status_port.open(status_port_name)
  pos_port=yarp.BufferedPortBottle()
  pos_port.open(pos_port_name)

  motx=Stepper(2, 3, 4, step=0.225)
  moty=Stepper(17, 27, 22, step=0.225)
  motz=Stepper(10, 9, 11, step=0.1125) # half the step of the others because of the belt reduction factor
  #motz=Stepper(10, 9, 11)
  axisx=Axis(motx)
  axisy=Axis(moty)
  axisz=Axis(motz)
  axisx.enable()
  axisy.enable()
  axisz.enable()

  while True:
    input_bottle=input_port.read(False)
    if input_bottle:
      input_data=input_bottle.get(0).asString()
      print "Input data: ", input_data
      data=input_data.split(" ")
      #print "Data: ", data
      if data[0]=="speed":
        #print "Speed command: ", float(data[1]), float(data[2]), float(data[3])
        axisx.move(0.01, speed=float(data[1]))
        axisy.move(0.01, speed=float(data[2]))
        axisz.move(0.01, speed=float(data[3]))
      elif data[0]=="move":
        if (not motx.isBusy()) and (not moty.isBusy()) and (not motz.isBusy()):
          axisx.move(float(data[1]), speed=float(data[4]))
          axisy.move(float(data[2]), speed=float(data[4]))
          axisz.move(float(data[3]), speed=float(data[4]))
        else:
          print "Still executing previous command, ignoring new command"
      elif data[0]=="move_abs":
        if (not motx.isBusy()) and (not moty.isBusy()) and (not motz.isBusy()):
          axisx.move_abs(float(data[1]), speed=float(data[4]))
          axisy.move_abs(float(data[2]), speed=float(data[4]))
          axisz.move_abs(float(data[3]), speed=float(data[4]))
        else:
          print "Still executing previous command, ignoring new command"
      elif data[0]=="status":
        busy=motx.isBusy() or moty.isBusy() or motz.isBusy()
        status_bottle=status_port.prepare()
        status_bottle.clear()
        status_bottle.addInt(int(busy))
        status_port.write()
      elif data[0]=="stop":
        print "stop"
        motx.stop()
        moty.stop()
        motz.stop()
      elif data[0]=="enable":
        print "Enable"
        motx.enable()
        moty.enable()
        motz.enable()
      elif data[0]=="up":
        print "Pull drill up"
        raw_input()
      elif data[0]=="down":
        print "Pull drill down"
        raw_input()
      elif data[0]=="cur_pos":
        print "Current Position"
        pos_bottle=pos_port.prepare()
        pos_bottle.clear()
        pos_bottle.addDouble(axisx.cur_pos)
        pos_bottle.addDouble(axisy.cur_pos)
        pos_bottle.addDouble(axisz.cur_pos)
        pos_bottle.addDouble(axisx.cur_pos/0.0254)
        pos_bottle.addDouble(axisy.cur_pos/0.0254)
        pos_bottle.addDouble(axisz.cur_pos/0.0254)
        pos_port.write()
      elif data[0]=="reset_pos":
        print "Resetting position!"
        motx.reset_pos()
        moty.reset_pos()
        motz.reset_pos()
    motx.update()
    moty.update()
    motz.update()
    axisx.update()
    axisy.update()
    axisz.update()
    yarp.Time.delay(0.00001)

  #circle1=Circle(axisx, axisy)
  #circle1.do_circle(0.01, cut_speed=0.0005, move_speed=0.05)
