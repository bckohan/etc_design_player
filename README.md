# etc_design_player
ETC Design Audio Playlist Player


## Installation

Replace 192.168.1.106 with the correct IP address for your raspberry pi below.

 - Build this package:
    `poetry build`
 - SCP this package to the device:
    `scp ./dist/etc_player-*.whl mvc@192.168.1.106:./`
    `scp ./install.sh mvc@192.168.1.106:./`
    `ssh mvc@192.168.1.106`
 - Install Package on Device:
    `raspberrypi> source ./install.sh`
