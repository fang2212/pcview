#!/usr/bin/env python
from __future__ import print_function

'''common utility functions'''

import math, os
import numpy as np

radius_of_earth = 6378137.0  # in meters
c_light = 299792458.0  # in m/s
pi = 3.1415926535897932384626433832795  # Definition of Pi used in the GPS coordinate system
deg2rad = (pi / 180.0)
rad2deg = (180.0 / pi)
arcs = (3600.0 * 180.0 / pi)

a_wgs84 = 6378137.0  # long radius of earth ellipsoid
b_wgs84 = 6356752.314245  # short radius of earth ellipsoid
e_wgs84 = ((a_wgs84 * a_wgs84 - b_wgs84 * b_wgs84) ** 0.5) / a_wgs84  # first eccentricity
f_wgs84 = 1.0 / 298.257223563  # Flattening
omega_wgs = 7.2921151467e-5  # the earth rotation rate
e2 = 0.00669437999013


def blh2xyz(latitude, longitude, height):
    """Convert BLH coordinates to XYZ.
    return tuple(X, Y, Z).
    Example 1, convert BJFS(Beijing, China) BLH to XYZ:
    XYZ position calculated by TEQC software:
    - X: -2148748
    - Y: 4426656
    - Z: 4044670
    # >>> x, y, z = blh2xyz(39.608611, 115.892456, 108.0420)
    # >>> round(x), round(y), round(z)
    (-2148748, 4426656, 4044670)
    Example 2, convert BOGT(Bogota, Colombia) BLH to XYZ:
    XYZ position calculated by TEQC software:
    - X: 1744394
    - Y: -6116025
    - Z: 512728
    # >>> x, y, z = blh2xyz(4.640045, -74.080950, 2563.1791)
    # >>> round(x), round(y), round(z)
    (1744394, -6116025, 512728)
    """
    # convert angle unit to radians
    latitude = math.radians(latitude)
    longitude = math.radians(longitude)

    e = math.sqrt(1 - (b_wgs84**2)/(a_wgs84**2))
    N = a_wgs84 / math.sqrt(1 - e**2 * math.sin(latitude)**2)
    # calculate X, Y, Z
    X = (N + height) * math.cos(latitude) * math.cos(longitude)
    Y = (N + height) * math.cos(latitude) * math.sin(longitude)
    Z = (N * (1 - e**2) + height) * math.sin(latitude)

    return X, Y, Z


def xyz2blh(x, y, z):
    """Convert XYZ coordinates to BLH,
    return tuple(latitude, longitude, height).
    Example 1, convert BJFS(Beijing, China) XYZ to BLH:
    BLH position calculated by TEQC software:
    - latitute: 39.6086
    - longitude: 115.8928
    - height: 112.78
    # >>> lat, lon, hgt = xyz2blh(-2148778.283, 4426643.490, 4044675.194)
    # >>> round(lat, 4), round(lon, 4), round(hgt, 2)
    (39.6086, 115.8928, 112.78)
    Example 2, convert BOGT(Bogota, Colombia) XYZ to BLH:
    BLH position calculated by TEQC software:
    - latitute: 4.6401
    - longitude: -74.0806
    - height: 2585.69
    # >>> lat, lon, hgt = xyz2blh(1744433.521, -6116034.660, 512736.584)
    # >>> round(lat, 4), round(lon, 4), round(hgt, 2)
    (4.6401, -74.0806, 2585.69)
    """
    e = math.sqrt(1 - (b_wgs84**2)/(a_wgs84**2))
    # calculate longitude, in radians
    longitude = math.atan2(y, x)

    # calculate latitude, in radians
    xy_hypot = math.hypot(x, y)

    lat0 = 0
    latitude = math.atan(z / xy_hypot)

    while abs(latitude - lat0) > 1E-9:
        lat0 = latitude
        N = a_wgs84 / math.sqrt(1 - e**2 * math.sin(lat0)**2)
        latitude = math.atan((z + e**2 * N * math.sin(lat0)) / xy_hypot)
    # calculate height, in meters
    height = z / math.sin(latitude) - N * (1 - e**2)
    # convert angle unit to degrees
    longitude = math.degrees(longitude)
    latitude = math.degrees(latitude)

    return latitude, longitude, height


def xyz2neu(x0, y0, z0, x, y, z):
    """Convert cartesian coordinate system to site-center system.
    Input paraments:
    - x0, y0, z0: coordinate of centra site,
    - x, y, z: coordinate to be converted.
    Example: Use coordinate of BJFS IGS site
    # >>> north, east, up = xyz2neu(-2148747.998, 4426652.444, 4044675.151,
    # ... -2148745.727, 4426649.545, 4044668.469)
    # >>> round(north, 2), round(east, 2), round(up, 2)
    (-2.85, -0.78, -7.03)
    """
    # calculate the lat, lon and height of center site
    lat, lon, _ = xyz2blh(x0, y0, z0)
    # convert angle unit to radians
    lat, lon = math.radians(lat), math.radians(lon)
    # calculate NEU
    north = (-math.sin(lat) * math.cos(lon) * (x - x0) -
             math.sin(lat) * math.sin(lon) * (y - y0) +
             math.cos(lat) * (z - z0))
    east = -math.sin(lon) * (x - x0) + math.cos(lon) * (y - y0)
    up = (math.cos(lat) * math.cos(lon) * (x - x0) +
          math.cos(lat) * math.sin(lon) * (y - y0) +
          math.sin(lat) * (z - z0))

    return north, east, up


def ned2blh(blh0: np.array, ned: np.array) -> np.array:
    """
    calculates the blh coordinate of the given ned target
    """
    blh0[0] = blh0[0] * deg2rad
    lat0 = blh0[0]
    blh0[1] = blh0[1] * deg2rad
    drinv = np.zeros((3, 3))
    rm = a_wgs84 * (1 - e2) / pow(1 - e2 * math.sin(lat0) * math.sin(lat0), 1.5)
    rn = a_wgs84 / math.sqrt(1 - e2 * math.sin(lat0) * math.sin(lat0))
    drinv[0, 0] = 1 / (rm + blh0[2])
    drinv[1, 1] = 1 / (rn + blh0[2]) / math.cos(lat0)
    drinv[2, 2] = -1
    target_blh = np.dot(drinv, ned) + blh0
    target_blh[0] = target_blh[0] * rad2deg
    target_blh[1] = target_blh[1] * rad2deg
    return target_blh


def enu2blh(blh0: np.array, enu: np.array) -> np.array:
    """
    calculates the blh coordinate of the given ned target
    """
    blh0[0] = blh0[0] * deg2rad
    lat0 = blh0[0]
    blh0[1] = blh0[1] * deg2rad
    drinv = np.zeros((3, 3))
    rm = a_wgs84 * (1 - e2) / pow(1 - e2 * math.sin(lat0) * math.sin(lat0), 1.5)
    rn = a_wgs84 / math.sqrt(1 - e2 * math.sin(lat0) * math.sin(lat0))
    drinv[0, 0] = 1 / (rn + blh0[2]) / math.cos(lat0)
    drinv[1, 1] = 1 / (rm + blh0[2])
    drinv[2, 2] = 1
    target_blh = np.dot(drinv, enu) + blh0
    target_blh[0] = target_blh[0] * rad2deg
    target_blh[1] = target_blh[1] * rad2deg
    return target_blh


def body2enu(target_pos: np.array, body_atti: np.array):
    """
    target_pos: target position in (front, right, up) axis
    body_atti: (yaw, pitch, roll) rotation to NED
    """
    pass


def body2enu_2d(target_pos: np.array, body_atti: np.array):
    pass



def body2blh(pos_body: np.array, atti_body: np.array, target_body: np.array):
    pass

def gps_distance(lat1, lon1, lat2, lon2):
    '''return distance between two points in meters,
    coordinates are in degrees
    thanks to http://www.movable-type.co.uk/scripts/latlong.html'''
    from math import radians, cos, sin, sqrt, atan2
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    dLat = lat2 - lat1
    dLon = lon2 - lon1

    a = sin(0.5 * dLat) ** 2 + sin(0.5 * dLon) ** 2 * cos(lat1) * cos(lat2)
    c = 2.0 * atan2(sqrt(a), sqrt(1.0 - a))
    return radius_of_earth * c


def gps_bearing(lat1, lon1, lat2, lon2):
    '''return bearing between two points in degrees, in range 0-360
    thanks to http://www.movable-type.co.uk/scripts/latlong.html'''
    from math import sin, cos, atan2, radians, degrees
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    dLat = lat2 - lat1
    dLon = lon2 - lon1
    y = sin(dLon) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dLon)
    bearing = degrees(atan2(y, x))
    if bearing < 0:
        bearing += 360.0
    return bearing


class PosLLH:
    '''a class for latitude/longitude/altitude'''

    def __init__(self, lat, lon, alt):
        self.lat = lat
        self.lon = lon
        self.alt = alt

    def __str__(self):
        return '(%.8f, %.8f, %.8f)' % (self.lat, self.lon, self.alt)

    def ToECEF(self):
        '''convert from lat/lon/alt to ECEF

        Thanks to Nicolas Hennion
        http://www.nicolargo.com/dev/xyz2lla/
        '''
        from math import sqrt, pow, sin, cos
        a = 6378137.0
        e = 8.1819190842622e-2

        lat = self.lat * (pi / 180.0)
        lon = self.lon * (pi / 180.0)
        alt = self.alt

        n = a / sqrt((1.0 - pow(e, 2) * pow(sin(lat), 2)))
        x = (n + alt) * cos(lat) * cos(lon)
        y = (n + alt) * cos(lat) * sin(lon)
        z = (n * (1 - pow(e, 2)) + alt) * sin(lat)

        return PosVector(x, y, z)

    def distance(self, pos):
        '''return distance to another position'''
        if isinstance(pos, PosLLH):
            pos = pos.ToECEF()
        return self.ToECEF().distance(pos)

    def distanceXY(self, pos):
        '''return distance to another position'''
        if isinstance(pos, PosLLH):
            pos = pos.ToECEF()
        return self.ToECEF().distanceXY(pos)


class PosVector:
    '''a X/Y/Z vector class, used for ECEF positions'''

    def __init__(self, X, Y, Z, extra=None):
        self.X = float(X)
        self.Y = float(Y)
        self.Z = float(Z)
        # allow for some extra information to be carried in the vector
        self.extra = extra

    def __str__(self):
        return '(%.8f, %.8f, %.8f)' % (self.X, self.Y, self.Z)

    def __add__(self, v):
        return PosVector(self.X + v.X,
                         self.Y + v.Y,
                         self.Z + v.Z)

    def __mul__(self, v):
        return PosVector(self.X * v,
                         self.Y * v,
                         self.Z * v)

    def __div__(self, v):
        return PosVector(self.X / v,
                         self.Y / v,
                         self.Z / v)

    def distance(self, pos2):
        import math
        if isinstance(pos2, PosLLH):
            pos2 = pos2.ToECEF()
        return math.sqrt((self.X - pos2.X) ** 2 +
                         (self.Y - pos2.Y) ** 2 +
                         (self.Z - pos2.Z) ** 2)

    def distanceXY(self, pos2):
        import math
        if isinstance(pos2, PosLLH):
            pos2 = pos2.ToECEF()
        llh1 = self.ToLLH()
        llh2 = pos2.ToLLH()
        alt = (llh1.alt + llh2.alt) * 0.5
        llh1.alt = alt
        llh2.alt = alt
        return llh1.distance(llh2)

    def bearing(self, pos):
        '''return bearing between two points in degrees, in range 0-360
        thanks to http://www.movable-type.co.uk/scripts/latlong.html'''
        from math import sin, cos, atan2, radians, degrees
        llh1 = self.ToLLH()
        llh2 = pos.ToLLH()

        lat1 = radians(llh1.lat)
        lat2 = radians(llh2.lat)
        lon1 = radians(llh1.lon)
        lon2 = radians(llh2.lon)
        dLat = lat2 - lat1
        dLon = lon2 - lon1
        y = sin(dLon) * cos(lat2)
        x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dLon)
        bearing = degrees(atan2(y, x))
        if bearing < 0:
            bearing += 360.0
        return bearing

    def offsetXY(self, pos):
        '''
	return offset X,Y in meters to pos
	'''
        from math import sin, cos, radians
        distance = self.distanceXY(pos)
        bearing = self.bearing(pos)
        x = distance * sin(radians(bearing))
        y = distance * cos(radians(bearing))
        return (x, y)

    def SagnacCorrection(self, pos2):
        '''return the Sagnac range correction. Based
           on on RTCM2.3 appendix C. Note that this is not a symmetric error!
	   The pos2 position should be the satellite
        '''
        OMGE = 7.2921151467e-5  # earth angular velocity (IS-GPS) (rad/s)
        return OMGE * (pos2.X * self.Y - pos2.Y * self.X) / c_light

    def distanceSagnac(self, pos2):
        '''return distance taking into account Sagnac effect. Based
           on geodist() in rtklib. Note that this is not a symmetric distance!
	   The pos2 position should be the satellite

	   Note that the Sagnac distance is an alternative to rotating
	   the satellite positions using
	   rangeCorrection.correctPosition(). Only one of them should
	   be used
        '''
        return self.distance(pos2) + self.SagnacCorrection(pos2)

    def ToLLH(self):
        '''convert from ECEF to lat/lon/alt

        Thanks to Nicolas Hennion
        http://www.nicolargo.com/dev/xyz2lla/
        '''
        from math import sqrt, pow, cos, sin, pi, atan2

        a = radius_of_earth
        e = 8.1819190842622e-2

        b = sqrt(pow(a, 2) * (1 - pow(e, 2)))
        ep = sqrt((pow(a, 2) - pow(b, 2)) / pow(b, 2))
        p = sqrt(pow(self.X, 2) + pow(self.Y, 2))
        th = atan2(a * self.Z, b * p)
        lon = atan2(self.Y, self.X)
        lat = atan2((self.Z + ep * ep * b * pow(sin(th), 3)), (p - e * e * a * pow(cos(th), 3)))
        n = a / sqrt(1 - e * e * pow(sin(lat), 2))
        alt = p / cos(lat) - n
        lat = (lat * 180) / pi
        lon = (lon * 180) / pi
        return PosLLH(lat, lon, alt)


def ParseLLH(pos_string):
    '''parse a lat,lon,alt string and return a PosLLH'''
    a = pos_string.split(',')
    if len(a) != 3:
        return None
    return PosLLH(float(a[0]), float(a[1]), float(a[2]))


def correctWeeklyTime(time):
    '''correct the time accounting for beginning or end of week crossover'''
    half_week = 302400  # seconds
    corrTime = time
    if time > half_week:
        corrTime = time - 2 * half_week
    elif time < -half_week:
        corrTime = time + 2 * half_week
    return corrTime


def gpsTimeToTime(week, sec):
    '''convert GPS week and TOW to a time in seconds since 1970'''
    epoch = 86400 * (10 * 365 + (1980 - 1969) / 4 + 1 + 6 - 2)
    return epoch + 86400 * 7 * week + sec


def saveObject(filename, object):
    '''save an object to a file'''
    import pickle
    h = open(filename + '.tmp', mode='wb')
    pickle.dump(object, h)
    h.close()
    os.rename(filename + '.tmp', filename)


def loadObject(filename):
    '''load an object from a file'''
    import pickle
    try:
        h = open(filename, mode='rb')
        obj = pickle.load(h)
        h.close()
        return obj
    except Exception as e:
        return None


if __name__ == '__main__':
    a = np.array([114.0, 22.0, 1.0])
    ned = np.array([10, 5, -2.0])
    t = ned2blh(a, ned)
    print(t)
    # llh = PosLLH(22.540219, 113.947425, 115.347)
    # ecef = llh.ToECEF()
    # print(ecef)
    # ecef1 = PosVector(40557340.0, 5386562.5, 2429815.25)
    # print(ecef.ToLLH())
