#!/usr/bin/python

from gpiozero import DigitalOutputDevice as dig
from gpiozero import DigitalOutputDevice as pwm
from time import sleep
import time
from multiprocessing import Process, Queue
from math import sqrt, atan, pi, cos, sin
from numpy import arctan2, floor, array
from misc import Angle, create_object_vis, set_axis_vis, set_cmd_vis

input_port_name="/cnc/cmd:i"
status_port_name="/cnc/status:o"
pos_port_name="/cnc/pos:o"

#X inverted
#Y inverted
#Z inverted

speed_scale=1.0

def arc_point_to_angle(center_x, center_y, x, y):
    return(Angle(arctan2(y-center_y, x-center_x)))

def gen_arc(cur_x, cur_y, cur_z, x, y ,z, i, j, res, speed, angle_res_factor=1.0, cw=True):
    center_x=cur_x+i
    center_y=cur_y+j
    radius=sqrt(i**2+j**2)
    arc_length=2.0*pi*radius
    #print "Radius: ", radius, " Radius pos: ", center_x, center_y
    #print "Initial pos: ", cur_x, cur_y, cur_z
    angle_res=Angle(angle_res_factor*atan(res/radius)*360.0/(2.*pi))
    #print "Angle resolution: ", angle_res
    start_angle=arc_point_to_angle(center_x, center_y, cur_x, cur_y)
    end_angle=arc_point_to_angle(center_x, center_y, x, y)
    #print "Start angle: ", start_angle
    #print "Stop angle: ", end_angle
    angle_diff=end_angle-start_angle
    #print "Angle difference: ", angle_diff
    angles=floor(angle_diff/angle_res.angle)+1
    #print "Angles: ", angles
    #get points in angle range
    z_step=(z-cur_z)/angles
    #print "Z step: ", z_step
    inside=True
    angle=start_angle
    arc_points=[]
    arc_x=cur_x
    arc_y=cur_y
    arc_z=cur_z
    while True:
        if cw:
            angle-=angle_res
            if not angle.between(end_angle, start_angle):
                #print "angle outside, finishing"
                break
        else:
            angle+=angle_res
            if not angle.between(start_angle, end_angle):
                #print "angle outside, finishing"
                break
        #print "Current angle: ", angle

        old_arc_x=arc_x
        old_arc_y=arc_y
        old_arc_z=arc_z

        arc_x=radius*cos(angle.angle)+center_x
        arc_y=radius*sin(angle.angle)+center_y
        arc_z=arc_z+z_step

        d=sqrt((arc_x-old_arc_x)**2+(arc_y-old_arc_y)**2+(arc_z-old_arc_z)**2)
        speedx=float(speed)*abs((arc_x-old_arc_x)/d)
        speedy=float(speed)*abs((arc_y-old_arc_y)/d)
        speedz=float(speed)*abs((arc_z-old_arc_z)/d)

        #print "Next pos: ", arc_x, arc_y, arc_z, speedx, speedy, speedz
        arc_points.append([arc_x,arc_y,arc_z, speedx, speedy, speedz])
    d=sqrt((x-arc_x)**2+(y-arc_y)**2+(z-arc_z)**2)
    speedx=float(speed)*abs((x-arc_x)/d)
    speedy=float(speed)*abs((y-arc_y)/d)
    speedz=float(speed)*abs((z-arc_z)/d)
    arc_points.append([x, y, z, speedx, speedy, speedz])
    #print "Last pos: ", x, y , z, speedx, speedy, speedz
    #print "Arc points: ", len(arc_points)
    return(arc_points)


class Axis:
    def __init__(self, stepper, pitch=0.005, backlash=0.002):
        #pitch = meters per revolution
        self.pitch=pitch
        self.stepper=stepper
        self.backlash=backlash
        self.res=(self.stepper.step/360.)*self.pitch
        self.last_move_right=True
        self.changed_dir=False
        self.cur_pos=self.backlash/2.0
        self.cur_head_pos=self.cur_pos-self.backlash/2.0
        self.set_to(self.cur_head_pos)
        self.last_head_pos_before_change_dir=self.cur_head_pos
        #self.stepper.move_angle2(360.0*(self.cur_pos)/self.pitch, 0.001/self.pitch)

    def park(self, right=True):
        self.cur_pos=(self.stepper.cur_angle/360.0)*self.pitch
        print "Motor os before parking; ", self.cur_pos
        if right:
            self.stepper.move_angle2(360.0*(self.cur_pos+self.backlash)/self.pitch, 0.010/self.pitch)
            self.last_move_right=True
            self.cur_pos=(self.stepper.cur_angle/360.0)*self.pitch
            self.cur_head_pos=self.cur_pos-self.backlash/2.0
        else:
            self.stepper.move_angle2(360.0*(self.cur_pos-self.backlash)/self.pitch, 0.010/self.pitch)
            self.last_move_right=False
            self.cur_pos=(self.stepper.cur_angle/360.0)*self.pitch
            self.cur_head_pos=self.cur_pos+self.backlash/2.0
        self.last_head_pos_before_change_dir=self.cur_head_pos

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

    def move2(self, distance, speed=0.001):
        #print "moving relative: ", distance, self.cur_head_pos+distance
        self.move_abs2(self.cur_head_pos+distance, speed=speed)

    def move_abs(self, pos, speed=0.001):
        self.move(pos-self.cur_pos, speed)

    def move_abs2(self, pos, speed=0.001):
        #distance in meters!
        #speed in meters/second
        if speed<0.0:
          speed=-speed
        if speed==0.0:
          speed=0.000001
        if speed<0.000001:
            speed=0.000001
        #print "Moving: ", distance/self.pitch, " revolutions"
        offset=0.0
        if abs(pos-self.cur_head_pos)<self.res:
            return()
        if self.last_move_right:
            if (pos-self.cur_head_pos)>0.0:
                #print "Still moving right"
                offset=self.backlash/2.0
            elif (pos-self.cur_head_pos)<0.0:
                print "Changing direction from right to left"
                offset=-self.backlash/2.0
                self.last_move_right=False
                self.changed_dir=True
                self.stepper.backlash_speed=20.0
                self.last_head_pos_before_change_dir=self.cur_head_pos
                print "Last head pos: ", self.cur_head_pos
            else:
                print "No movement commanded"
                return()
        else:
            if (pos-self.cur_head_pos)<0.0:
                #print "Still moving left"
                offset=-self.backlash/2.0
            elif (pos-self.cur_head_pos)>0.0:
                print "Changing direction from left to right"
                offset=self.backlash/2.0
                self.last_move_right=True
                self.changed_dir=True
                self.stepper.backlash_speed=20.0
                self.last_head_pos_before_change_dir=self.cur_head_pos
                print "Last head pos: ", self.cur_head_pos
            else:
                print "No movement commanded"
                return()
        #print "Stepper move command pos: ", pos+offset, speed/self.pitch
        self.stepper.move_angle2(360.0*(pos+offset)/self.pitch, speed/self.pitch)

    def set_to(self, pos):
        if self.last_move_right:
            offset=self.backlash/2.0
        else:
            offset=-self.backlash/2.0
        self.stepper.set_to(360.0*(pos+offset)/self.pitch)

    def update(self):
        self.cur_pos=(self.stepper.cur_angle/360.0)*self.pitch
        if self.changed_dir: # it changed dir from last command and still hasn't overcomed backlash
            if ((not self.last_move_right) and ((self.cur_pos-self.last_head_pos_before_change_dir)>(-self.backlash/2.0)+(2*self.pitch*self.stepper.step/360.0))) or ((self.last_move_right) and ((self.cur_pos-self.last_head_pos_before_change_dir)<(self.backlash/2.0)-(2*self.pitch*self.stepper.step/360.0))):
                #print "Still inside backlash area", self.cur_pos-self.last_head_pos_before_change_dir, self.cur_pos, self.last_head_pos_before_change_dir
                self.cur_head_pos=self.last_head_pos_before_change_dir
            else:
                print "Out of backlash area", self.cur_pos-self.last_head_pos_before_change_dir, self.cur_pos, self.last_head_pos_before_change_dir
                self.changed_dir=False
                self.stepper.backlash_speed=1.0
        if not self.changed_dir:
            if self.last_move_right:
                self.cur_head_pos=self.cur_pos-self.backlash/2.0
            else:
                self.cur_head_pos=self.cur_pos+self.backlash/2.0
            self.last_head_pos_before_change_dir=self.cur_head_pos

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

class CNC_sim:
    def __init__(self):
        #step in degrees
        self.objects_port=yarp.BufferedPortBottle()

        objectportname="/simcnc/objects:o"
        objectvisportname="/myvis/roboviewer/objects:i"
        self.objects_port.open(objectportname)
        self.objects_port.setStrict(True)
        cstyle=yarp.ContactStyle()
        cstyle.persistent=True
        yarp.Network.connect(objectportname, objectvisportname, cstyle)
        #yarp.Network.connect(objectportname, "/tmp/port/1", cstyle)
        while not (yarp.Network.isConnected(objectportname, objectvisportname)):
            print "Waiting connection"
        self.cyl_obj_num=1
        create_object_vis(self.objects_port, self.cyl_obj_num, "cylinder", [0.0127/2, 0.0127/2, 0.0254*2], [0, 0, 0], [1, 0, 0])
        z_axis=array([0., 0., 0.0254*2])
        set_axis_vis(self.objects_port, self.cyl_obj_num, z_axis)
        self.cur_pos=array([0.,0.,1.])
        set_cmd_vis(self.objects_port, self.cyl_obj_num, "trans", self.cur_pos)
        set_cmd_vis(self.objects_port, self.cyl_obj_num, "timeout", [-1])

    def move(self, dist, axis):
        self.cur_pos[axis]=dist
        set_cmd_vis(self.objects_port, self.cyl_obj_num, "trans", self.cur_pos)


class Stepper_sim:
    def __init__(self, vis, axis=0, step=0.9, period=0.002):
        #step in degrees
        self.axis=axis
        self.vis=vis
        self.step=step
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
        self.ref_angle=0.0
        self.cur_angle=0.0
        self.cur_steps=0
        self.cur_dir=False
        self.last_vis_angle=0.0
        self.backlash_speed=1.0

    def reset_pos(self):
        self.cur_angle=0.0
        self.ref_angle=0.0
        self.cur_steps=0
        self.step_rest=0.0

    def set_to(self, angle):
        self.cur_angle=angle
        self.ref_angle=angle
        self.step_rest=0.0

    def enable(self):
        self._enable=True

    def is_moving(self):
        return(self.pulse._blink_thread.isAlive())

    def disable(self):
        self._enable=False

    def stop(self):
        self.disable()
        self.steps=0
        self.step_rest=0.0


    def move_angle2(self, angle, rps):
        #absolute
        self.ref_angle=angle
        self.period=1.0/(rps*360.0/self.step)

    def move_angle(self, delta_angle, rps):
        #angle in degrees
        #rps rev per second
        print "Moving: ", delta_angle/self.step, " steps"
        total_steps=self.step_rest+delta_angle/self.step
        step_rest=total_steps-float(int(total_steps))
        print "Total steps: ", total_steps, " step rest: ", step_rest
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
            self.time_last_toggle=new_time
            #print "Steps left: ", self.steps
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

    def update2(self):
      #print "Updating motor"
      if self._enable:
        new_time=time.time()
        if self.period==0.0:
            pass
        else:
          if (new_time-self.time_last_toggle)>=(self.period/(speed_scale*self.backlash_speed)):
            #print "*****Time to toggle! ", new_time-self.time_last_toggle
            self.time_last_toggle=new_time
            #print "Steps left: ", self.steps
            delta_angle=self.ref_angle-self.cur_angle
            #print "Delta angle: ", delta_angle
            if abs(delta_angle)>(self.step/2.0):
                #print "Correcting"
                if delta_angle>0:
                    if self.cur_dir==True:
                        self.cur_dir=False
                        sleep(0.00001)
                    self.cur_angle+=self.step
                else:
                    if self.cur_dir==False:
                        self.cur_dir=True
                        sleep(0.00001)
                    self.cur_angle-=self.step
                #print "Cur angle: ", self.cur_angle
                if abs(self.cur_angle-self.last_vis_angle)>10.0:
                    #print "Visualizing angle. ", self.cur_angle
                    self.vis.move(self.cur_angle*0.0001, self.axis)
                    self.last_vis_angle=self.cur_angle
            else:
                #print "Not correction, update vis now. ", self.cur_angle
                self.vis.move(self.cur_angle*0.0001, self.axis)
                self.last_vis_angle=self.cur_angle
      else:
          #print "Motor disabled"
          pass

    def isBusy2(self):
        if abs(self.ref_angle-self.cur_angle)>(self.step/2.0):
            #print "is busy2. Ref angle: ", self.ref_angle, " cur angle: ", self.cur_angle
            return(True)
        else:
            return(False)

    def isBusy(self):
        print "is Busy, steps: ", self.steps
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
        self.direction=dig(self.dir_pin, active_high=True)
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
        self.ref_angle=0.0
        self.cur_angle=0.0
        self.cur_steps=0
        self.cur_dir=False
        self.backlash_speed=1.0

    def reset_pos(self):
        self.cur_angle=0.0
        self.ref_angle=0.0
        self.cur_steps=0
        self.step_rest=0.0

    def set_to(self, angle):
        self.cur_angle=angle
        self.ref_angle=angle
        self.step_rest=0.0

    def enable(self):
        self._enable=True
        self.ena.on()

    def is_moving(self):
        return(self.pulse._blink_thread.isAlive())

    def disable(self):
        self._enable=False
        self.ena.off()
        #self.direction.off()
        #self.pulse.off()

    def stop(self):
        self.disable()
        self.steps=0
        self.step_rest=0.0


    def move_angle2(self, angle, rps):
        #absolute
        self.ref_angle=angle
        self.period=1.0/(rps*360.0/self.step)

    def move_angle(self, delta_angle, rps):
        #angle in degrees
        #rps rev per second
        print "Moving: ", delta_angle/self.step, " steps"
        total_steps=self.step_rest+delta_angle/self.step
        step_rest=total_steps-float(int(total_steps))
        print "Total steps: ", total_steps, " step rest: ", step_rest
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
            self.time_last_toggle=new_time
            #print "Steps left: ", self.steps
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

    def update2(self):
      #print "Updating motor"
      if self._enable:
        new_time=time.time()
        if self.period==0.0:
          self.pulse.off()
        else:
          if (new_time-self.time_last_toggle)>=(self.period/(speed_scale*self.backlash_speed)):
            #print "*****Time to toggle! ", new_time-self.time_last_toggle
            self.time_last_toggle=new_time
            #print "Steps left: ", self.steps
            delta_angle=self.ref_angle-self.cur_angle
            #print "Delta angle: ", delta_angle
            if abs(delta_angle)>(self.step/2.0):
                #print "Correcting"
                if delta_angle>0:
                    if self.cur_dir==True:
                        self.direction.off()
                        self.cur_dir=False
                        sleep(0.00001)
                    self.cur_angle+=self.step
                else:
                    if self.cur_dir==False:
                        self.direction.on()
                        self.cur_dir=True
                        sleep(0.00001)
                    self.cur_angle-=self.step
                self.pulse.on()
                self.pulse.off()

    def isBusy2(self):
        if abs(self.ref_angle-self.cur_angle)>(self.step/2.0):
            return(True)
        else:
            return(False)

    def isBusy(self):
        print "is Busy, steps: ", self.steps
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
  input_port.setStrict()
  status_port=yarp.BufferedPortBottle()
  status_port.open(status_port_name)
  pos_port=yarp.BufferedPortBottle()
  pos_port.open(pos_port_name)
  sim=False
  if sim:
      cncsim=CNC_sim()
      motx=Stepper_sim(cncsim, axis=0, step=0.225)
      moty=Stepper_sim(cncsim, axis=1, step=0.225)
      motz=Stepper_sim(cncsim, axis=2, step=0.1125)
  else:
      motx=Stepper(2, 3, 4, step=0.225)
      moty=Stepper(17, 27, 22, step=0.225)
      motz=Stepper(10, 9, 11, step=0.1125) # half the step of the others because of the belt reduction factor
  #motz=Stepper(10, 9, 11)
  axisx=Axis(motx, backlash=0.00027)
  axisy=Axis(moty, backlash=0.00028)
  axisz=Axis(motz, backlash=0.00047)
  axisx.enable()
  axisy.enable()
  axisz.enable()
  busy=False
  counter=0
  move_buffer=[]
  while True:
    if len(move_buffer)>0:
        if not ((motx.isBusy2()) or (moty.isBusy2()) or (motz.isBusy2())):
            #print "Executing new move buffer cmd"
            ax, ay, az, speedx, speedy, speedz = move_buffer.pop(0)
            axisx.move_abs2(ax, speed=speedx)
            axisy.move_abs2(ay, speed=speedy)
            axisz.move_abs2(az, speed=speedz)
            axisx.update()
            axisy.update()
            axisz.update()
            motx.disable()
            moty.disable()
            motz.disable()
            if axisx.changed_dir: # if it must correct backlash, stop other axis meanwhile
                #print "Axis y, z waiting for x to correct backlash"
                motx.enable()
            if axisy.changed_dir:
                #print "Axis x, z waiting for y to correct backlash"
                moty.enable()
            if axisz.changed_dir:
                #print "Axis y, x waiting for z to correct backlash"
                motz.enable()
            if (not axisx.changed_dir) and (not axisy.changed_dir) and (not axisz.changed_dir):
                motx.enable()
                moty.enable()
                motz.enable()
            motx.update2()
            moty.update2()
            motz.update2()
            axisx.update()
            axisy.update()
            axisz.update()
            buffer_moving=True
    else:
        buffer_moving=False
    input_bottle=input_port.read(False)
    if input_bottle:
      input_data=input_bottle.get(0).asString()
      #print
      #print "Input data: ", input_data, busy
      data=input_data.split(" ")
      #print "Data: ", data
      if data[0]=="speed":
          print "Speed command: ", float(data[1]), float(data[2]), float(data[3])
          if float(data[1])<0.:
              axisx.move2(-0.01, speed=-float(data[1]))
          else:
              axisx.move2(0.01, speed=float(data[1]))
          if float(data[2])<0.:
              axisy.move2(-0.01, speed=-float(data[2]))
          else:
              axisy.move2(0.01, speed=float(data[2]))
          if float(data[3])<0.:
              axisz.move2(-0.01, speed=-float(data[3]))
          else:
              axisz.move2(0.01, speed=float(data[3]))
      elif data[0]=="move":
          if (not buffer_moving) and (not motx.isBusy2()) and (not moty.isBusy2()) and (not motz.isBusy2()):
              dx=float(data[1])
              dy=float(data[2])
              dz=float(data[3])
              d=sqrt((dx)**2+(dy)**2+(dz)**2)
              if d>0:
                  speedx=float(data[4])*abs((dx)/d)
                  speedy=float(data[4])*abs((dy)/d)
                  speedz=float(data[4])*abs((dz)/d)
                  #print "d: ", d, speedx, speedy, speedz
                  axisx.move2(dx, speed=speedx)
                  axisy.move2(dy, speed=speedy)
                  axisz.move2(dz, speed=speedz)
                  axisx.update()
                  axisy.update()
                  axisz.update()
              else:
                  print "Don't move!, already there!"
          else:
              print "Still executing previous command, ignoring new command"
      elif data[0]=="move_abs":
          print "Input data: ", data
          if (not buffer_moving) and (not motx.isBusy2()) and (not moty.isBusy2()) and (not motz.isBusy2()):
              x=float(data[1])
              y=float(data[2])
              z=float(data[3])
              d=sqrt((x-axisx.cur_head_pos)**2+(y-axisy.cur_head_pos)**2+(z-axisz.cur_head_pos)**2)
              if d>0:
                  speedx=float(data[4])*abs((x-axisx.cur_head_pos)/d)
                  speedy=float(data[4])*abs((y-axisy.cur_head_pos)/d)
                  speedz=float(data[4])*abs((z-axisz.cur_head_pos)/d)
                  #print "d: ", d, speedx, speedy, speedz
                  axisx.move_abs2(x, speed=speedx)
                  axisy.move_abs2(y, speed=speedy)
                  axisz.move_abs2(z, speed=speedz)
                  axisx.update()
                  axisy.update()
                  axisz.update()
              else:
                  print "Don't move!, already there!"
          else:
              print "Still executing previous command, ignoring new command"
      elif (data[0]=="move_abs_arc_cw") or (data[0]=="move_abs_arc_ccw"):
          if data[0]=="move_abs_arc_cw":
              cw=True
          else:
              cw=False
          print "Input data: ", data
          if (not buffer_moving) and (not motx.isBusy2()) and (not moty.isBusy2()) and (not motz.isBusy2()):
              x=float(data[1])
              y=float(data[2])
              z=float(data[3])
              i_arc=float(data[4])
              j_arc=float(data[5])
              speed=float(data[6])
              angle_res_factor=float(data[7])
              d=sqrt((x-axisx.cur_head_pos)**2+(y-axisy.cur_head_pos)**2+(z-axisz.cur_head_pos)**2)
              if d>0.0:
                  arc_cmd_list=gen_arc(axisx.cur_head_pos, axisy.cur_head_pos, axisz.cur_head_pos, x, y , z, i_arc, j_arc, axisx.res, speed, angle_res_factor, cw=cw)
                  move_buffer+=arc_cmd_list
                  #print "Buffer updated", move_buffer
                  # for ax,ay,az,speedx,speedy,speedz in arc_cmd_list:
                  #     print "Arc point: ", ax, ay, az
                  #     #raw_input()
                  #     axisx.move_abs2(ax, speed=speedx)
                  #     axisy.move_abs2(ay, speed=speedy)
                  #     axisz.move_abs2(az, speed=speedz)
                  #     motx.update2()
                  #     moty.update2()
                  #     motz.update2()
                  #     axisx.update()
                  #     axisy.update()
                  #     axisz.update()
                  #     while (motx.isBusy2()) or (moty.isBusy2()) or (motz.isBusy2()):
                  #         motx.update2()
                  #         moty.update2()
                  #         motz.update2()
                  #         axisx.update()
                  #         axisy.update()
                  #         axisz.update()
              else:
                  print "Don't move!, already there!"
          else:
              print "Still executing previous command, ignoring new command"
      elif data[0]=="status":
          #print "Status: ", motx.isBusy2(), moty.isBusy2(), motz.isBusy2()
          busy=motx.isBusy2() or moty.isBusy2() or motz.isBusy2() or buffer_moving
          status_bottle=status_port.prepare()
          status_bottle.clear()
          status_bottle.addInt(int(busy))
          status_port.writeStrict()
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
        print "Current Position", axisx.cur_head_pos, axisy.cur_head_pos, axisz.cur_head_pos, axisx.cur_pos, axisy.cur_pos, axisz.cur_pos
        pos_bottle=pos_port.prepare()
        pos_bottle.clear()
        pos_bottle.addDouble(axisx.cur_head_pos)
        pos_bottle.addDouble(axisy.cur_head_pos)
        pos_bottle.addDouble(axisz.cur_head_pos)
        pos_bottle.addDouble(axisx.cur_head_pos/0.0254)
        pos_bottle.addDouble(axisy.cur_head_pos/0.0254)
        pos_bottle.addDouble(axisz.cur_head_pos/0.0254)
        pos_port.writeStrict()
      elif data[0]=="park":
        axisx.park()
        axisy.park()
        axisz.park()
      elif data[0]=="reset_pos":
        print "Resetting position!"
        axisx.set_to(0.0)
        axisy.set_to(0.0)
        axisz.set_to(0.0)
      elif data[0]=="reset_z":
          print "input data: ", data
          z=float(data[1])
          print "Reset z to: ", z
          axisz.set_to(z)
      elif data[0]=="speed_scale":
          global speed_scale
          speed_scale=float(data[1])
          print "input data: ", data, " new speed scale: ", speed_scale
    if counter>1000:
          counter=0
          #print "Status: ", motx.isBusy2(), moty.isBusy2(), motz.isBusy2(), " Cur ref: ", motx.ref_angle, moty.ref_angle, motz.ref_angle, " Cur angle: ", motx.cur_angle, moty.cur_angle, motz.cur_angle
          busy=buffer_moving or motx.isBusy2() or moty.isBusy2() or motz.isBusy2()
          #status_bottle=status_port.prepare()
          #status_bottle.clear()
          #status_bottle.addInt(int(busy))
          #status_port.write()
    counter+=1
    motx.disable()
    moty.disable()
    motz.disable()
    if axisx.changed_dir: # if it must correct backlash, stop other axis meanwhile
        #print "Axis y, z waiting for x to correct backlash"
        motx.enable()
    if axisy.changed_dir:
        #print "Axis x, z waiting for y to correct backlash"
        moty.enable()
    if axisz.changed_dir:
        #print "Axis y, x waiting for z to correct backlash"
        motz.enable()
    if (not axisx.changed_dir) and (not axisy.changed_dir) and (not axisz.changed_dir):
        motx.enable()
        moty.enable()
        motz.enable()
    #print "motx update"
    motx.update2()
    #print "moty update"
    moty.update2()
    #print "motz update"
    motz.update2()
    #print "axisx update"
    axisx.update()
    #print "axisy update"
    axisy.update()
    #print "axisz update"
    axisz.update()
    yarp.Time.delay(0.0001)

  #circle1=Circle(axisx, axisy)
  #circle1.do_circle(0.01, cut_speed=0.0005, move_speed=0.05)
