# etc_design_player
ETC Design Audio Playlist Player


## Installation

Install the Raspberry PI operating system and connect it to your local network.
Determine the Raspberry PI's IP address - [there are numerous ways to do this](https://letmegooglethat.com/?q=How+do+I+determine+my+Raspberry+PI%27s+IP+address%3F).
Replace 192.168.1.106 with the correct IP address for your raspberry pi below 
when following this procedure:

 - Download the [latest package](https://github.com/bckohan/etc_design_player/blob/main/etc_player.zip).
 - Install the package (via Raspberry PI Desktop):
    * Unzip the downloaded package.
    * Double click on the install.sh file and select "execute in terminal".
 - Install the package (via terminal, replace IP with your raspberry pi's IP address):
    * `scp ~/Downloads/etc_player.zip mvc@192.168.1.106:./`
    * `ssh mvc@192.168.1.106`
    * `mvc@raspberrypi:~ $> gunzip ./etc_player.zip`
    * `mvc@raspberrypi:~ $> cd ./etc_player`
    * `mvc@raspberrypi:~ $> ./install.sh`
 - Follow all prompts.
 - Configure your playback: http://192.168.1.106/admin
