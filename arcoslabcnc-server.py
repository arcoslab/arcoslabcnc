#!/usr/bin/python

from gpiozero import DigitalOutputDevice as dig
from gpiozero import DigitalOutputDevice as pwm
from time import sleep
import time
from math import pi, atan, sin, cos
from multiprocessing import Process, Queue
input_port_name="/cnc/cmd:i"


def frange(x, y, jump):
  while x < y:
    yield x
    x += jump

class Circle:
    def __init__(self, axisx, axisy):
        self.axisx=axisx
        self.axisy=axisy
        self.step_x=self.axisx.stepper.step
        self.step_y=self.axisy.stepper.step
        self.pitch_x=self.axisx.pitch
        self.pitch_y=self.axisy.pitch
        self.res_x=(self.step_x/360.)*self.pitch_x
        self.res_y=(self.step_y/360.)*self.pitch_y
        self.move_speed=0.05
        self.cut_speed=0.03

    def do_circle(self, radius, cut_speed=0.03, move_speed=0.05):
        self.axisx.enable()
        self.axisy.enable()
        step_angle=atan(self.res_x/radius)*360.0/(2.*pi)
        print "Step angle: ", step_angle
        old_x=0.0
        old_y=0.0
        iteration=0
        for angle in frange(0., 360.0, step_angle):
            x=radius*cos(angle*(2*pi)/360.0)
            y=radius*sin(angle*(2*pi)/360.0)
            if iteration==0:
                print "Position piece in circle center"
                print "Moving to first circle position, pull bit up!"
                raw_input()
                iteration=1
                speed=move_speed
            elif iteration==1:
                print "Start mill position, pull bit down at desired height!"
                raw_input()
                iteration=2
                speed=cut_speed

            #print "Angle: ", angle, "X, Y: ", x, y, x-old_x, y-old_y
            #raw_input()
            self.axisx.move(x-old_x, speed)
            self.axisy.move(y-old_y, speed)
            while self.axisx.is_moving():
                print "Waiting for X"
                sleep(0.001)
                pass
            while self.axisy.is_moving():
                print "Waiting for Y"
                sleep(0.001)
                pass
            old_x=x
            old_y=y
        print "Pull bit up!, moving fast to center"
        raw_input()
        speed=move_speed
        self.axisx.move(-radius, speed)
        while self.axisx.is_moving():
            print "Waiting for X"
            sleep(0.001)
            pass

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

    def move_angle(self, delta_angle, rps):
        #angle in degrees
        #rps rev per second
        #print "Moving: ", delta_angle/self.step, " steps"
        total_steps=self.step_rest+delta_angle/self.step
        step_rest=total_steps-float(int(total_steps))
        #print "Total steps: ", total_steps, " step rest: ", step_rest
        if step_rest>=0.5:
            #print "Stepping one more!"
            steps=int(total_steps)+1
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
            else:
            #    print "Neg dir"
                self.direction.off()
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

  motx=Stepper(25, 8, 7)
  moty=Stepper(14, 15, 18)
  axisx=Axis(motx)
  axisy=Axis(moty)
  axisx.enable()
  axisy.enable()

  while True:
    input_bottle=input_port.read(False)
    if input_bottle:
      input_data=input_bottle.get(0).asString()
      print "Input data: ", input_data
      data=input_data.split(" ")
      #print "Data: ", data
      if data[0]=="speed":
        #print "Speed command: ", float(data[1]), float(data[2])
        axisx.move(0.01, speed=float(data[1]))
        axisy.move(0.01, speed=float(data[2]))
      elif data[0]=="move":
        axisx.move(float(data[1]), speed=float(data[3]))
        axisy.move(float(data[2]), speed=float(data[3]))
    motx.update()
    moty.update()
    yarp.Time.delay(0.0001)

  #circle1=Circle(axisx, axisy)
  #circle1.do_circle(0.01, cut_speed=0.0005, move_speed=0.05)
