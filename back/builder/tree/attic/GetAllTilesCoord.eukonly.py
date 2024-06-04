#!/usr/bin/python
import math


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0**zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int(
        (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi)
        / 2.0
        * n
    )
    return [xtile, ytile]


zoom = False
lat = False
lon = False

coo = open("XYZcoordinates", "w")
##output


def getXYZ(fi):
    with open(fi) as f:
        for line in f:
            tmp = line.split(":")
            if len(tmp) > 1:
                key = tmp[0].replace('"', "").replace(" ", "")
                val = tmp[1].replace('"', "").replace(" ", "").replace(",", "").rstrip()
                if key == "zoom":
                    zoom = val
                if key == "lat":
                    lat = val
                if key == "lon":
                    lon = val
                    # do stuff
                    if int(zoom) <= 20:
                        # 						print zoom
                        xy = deg2num(float(lat), float(lon), float(zoom))
                        coo.write("%d %d %s\n" % (xy[0], xy[1], zoom))
                        if int(zoom) >= 5:
                            xy2 = deg2num(float(lat), float(lon), float(int(zoom) - 1))
                            xy3 = deg2num(float(lat), float(lon), float(int(zoom) - 2))
                            xy4 = deg2num(float(lat), float(lon), float(int(zoom) - 3))
                            coo.write("%d %d %d\n" % (xy2[0], xy2[1], int(zoom) - 1))
                            coo.write("%d %d %d\n" % (xy3[0], xy3[1], int(zoom) - 2))
                            coo.write("%d %d %d\n" % (xy4[0], xy4[1], int(zoom) - 3))
                    zoom = False
                    lat = False
                    lon = False


# getXYZ('TreeFeatures1.json')
getXYZ("TreeFeatures2.json")
# getXYZ('TreeFeatures3.json')

coo.close()
