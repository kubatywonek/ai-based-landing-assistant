#!/bin/bash

echo "Running FlightGear with cessna 172p (c172x), rate 60, listening on localhost:5550..."

/Applications/FlightGear.app/Contents/MacOS/FlightGear \
  --fdm=null \
  --native-fdm=socket,in,60,,5550,udp \
  --aircraft=c172p \
  --airport=KSEA \
  --timeofday=noon \
  --prop:/sim/current-view/view-number=1 \
  --disable-sound \
  --disable-splash-screen \
  --disable-real-weather-fetch \
  --disable-clouds \
  --disable-random-objects \
  --disable-random-buildings \
  --disable-random-vegetation \
  --disable-specular-highlight \
  --disable-ai-traffic
