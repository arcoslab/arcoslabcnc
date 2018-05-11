from numpy import pi

class Angle(object):
    def __init__(self, angle=0.0):
        self.min_angle=0.0
        self.max_angle=2.0*pi
        self._set_angle(angle)

    def _get_angle(self):
        return(self._angle)

    def set_max_angle(self, max_angle):
        self.max_angle=max_angle

    def set_min_angle(self, min_angle):
        self.min_angle=min_angle

    def _set_angle(self, angle):
        angle-= float((int(angle/(self.max_angle))))*self.max_angle
        if angle<self.min_angle:
            angle+=self.min_angle+2.0*pi
        #print "Angle between 0 and 2*pi: ", angle
        self._angle=angle

    angle = property(_get_angle, _set_angle)

    def __add__(self, angle):
        temp=Angle()
        temp.max_angle=self.max_angle
        temp.min_angle=self.min_angle
        temp.angle=self.angle+angle.angle
        return(temp)

    def __sub__(self, angle):
        temp=Angle()
        temp.angle=self.angle-angle.angle
        return(temp)

    def __mul__(self, number):
        ''' Returns a normal number '''
        return(self.angle*number)

    def __div__(self, number):
        ''' Returns a normal number because this is used for angle speeds that can be bigger than 360degrees/s'''
        return(self.angle/number)

    def between(self, angle1, angle2, direction=True):
        ''' Returns true if current angle is between angle1 and angle2. Direction==True is positive '''
        if direction:
            _angle1=angle1.angle
            _angle2=angle2.angle
        else:
            _angle2=angle1.angle
            _angle1=angle2.angle

        if (_angle2-_angle1)>=0.0:
            # Not crosing zero
            if ((self.angle-_angle1) >= 0.0) and ((_angle2-self.angle) >= 0.0):
                return(True)
            else:
                return(False)
        else:
            if ((self.angle-_angle1) >= 0.0) or ((_angle2-self.angle) >= 0.0):
                return(True)
            else:
                return(False)

    def __repr__(self):
        return(str(self.angle)+", "+str(self.angle*180.0/pi))
