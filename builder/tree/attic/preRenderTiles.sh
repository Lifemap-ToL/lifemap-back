#!/bin/sh
/opt/mod_tile/render_list -n 7 < /usr/local/lifemap/XYZcoordinates >> /usr/local/lifemap/tilerenderer.log
/opt/mod_tile/render_list -m onlylabels -n 7 < /usr/local/lifemap/XYZcoordinates >> /usr/local/lifemap/tilerenderer.log
/opt/mod_tile/render_list -m nolabels -n 7 < /usr/local/lifemap/XYZcoordinates >> /usr/local/lifemap/tilerenderer.log

