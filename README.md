# etc_design_player
ETC Design Audio Playlist Player


## Installation

Install the Raspberry PI operating system and connect it to your local network.
Determine the Raspberry PI's IP address - [there are numerous ways to do this](https://letmegooglethat.com/?q=How+do+I+determine+my+Raspberry+PI%27s+IP+address%3F).
Replace 192.168.1.106 with the correct IP address for your raspberry pi below 
when following this procedure:

 - Download the latest package.
 - Install the package:
    * `scp ~/Downloads/etc_player-*.whl mvc@192.168.1.106:./`
    * `scp ./install.sh mvc@192.168.1.106:./`
    * `ssh mvc@192.168.1.106`
    * `mvc@raspberrypi:~ $> source ./install.sh`
 - Follow all prompts.
 - Configure your playback: http://192.168.1.106/admin

