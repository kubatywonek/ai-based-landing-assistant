@echo off
SET FGFS_PATH="C:\Program Files\FlightGear 2024.1\bin\fgfs.exe"

%FGFS_PATH% ^
  --fdm=null ^
  --native-fdm=socket,in,60,,5550,udp ^
  --aircraft=c172p ^
  --airport=KSEA ^
  --timeofday=noon ^
  --prop:/sim/current-view/view-number=1 ^
  --disable-sound ^
  --disable-splash-screen ^
  --disable-real-weather-fetch ^
  --disable-clouds ^
  --disable-random-objects ^
  --disable-random-buildings ^
  --disable-random-vegetation ^
  --disable-specular-highlight ^
  --disable-ai-traffic