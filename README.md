# etc_design_player
ETC Design Audio Playlist Player


## Installation

 - Build this package:
    `poetry build`
 - SCP this package to the device:
    `scp ./dist/etc_design_player-0.1.0-py3-none-any.whl mvc@192.168.1.106:./`
 - Install PyAudio on Device:
    `raspberrypi> sudo apt install python3-pyaudio`
 - Install package on Device:
    `raspberrypi> sudo pip3 install ./etc_design_player-0.1.0-py3-none-any.whl`
