# etc_design_player

Use [Raspberry Pi](https://www.raspberrypi.com/) to play audio wave files on a 
configurable schedule or on demand via a web interface. This software was 
originally developed to time the audio playback of museum exhibit audio tracks
with the opening schedule of the museum.


## Installation

Install the Raspberry Pi operating system and connect it to your local network.
Change the hostname of your Raspberry Pi to a memorable unique name - this name
will be used access the scheduler later. The hostname can be changed by clicking
the raspberry in the upper left menue and selecting "Preferences" -> 
"Raspberry Pi Configuration" -> "System" -> "Hostname". Click save and reboot.


 - Download the [latest package](https://github.com/bckohan/etc_design_player/raw/main/etc_player.zip).
 - To install from the Raspberry Pi Desktop:
    * Unzip the downloaded package.
    * Double click on the install.sh file and select "execute in terminal".
 - To install from your computer's terminal: (replace IP and "pi" with your 
   Raspberry Pi's IP address and username respectively). 
   [You will also need to enable ssh on your pi](https://letmegooglethat.com/?q=enable+ssh+on+raspberry+pi)
   and determine the Raspberry Pi's IP address - [there are numerous ways to do this](https://letmegooglethat.com/?q=How+do+I+determine+my+Raspberry+PI%27s+IP+address%3F).
   
    * `scp ~/Downloads/etc_player.zip pi@192.168.1.106:./`
    * `ssh pi@192.168.1.106`
    * `pi@raspberrypi:~ $> gunzip ./etc_player.zip`
    * `pi@raspberrypi:~ $> cd ./etc_player`
    * `pi@raspberrypi:~ $> ./install.sh`
 - After a few minutes the install script will prompt you to enter a username
   and password. This will be the account you use to login to the web interface
   to configure the playback. Once the install script disappears the install
   is complete.
 - To configure your playback from a computer on the same wifi network you can
   access from: http://<hostname>/admin where hostname is the hostname you set
   earlier or if on your Raspberry Pi's desktop you may also use
   http://localhost/admin

## Usage

Most wifi networks will allow you to access the scheduler interface through
`http://<hostname>/admin`. If this does not work you may need to use the IP
address instead. As mentioned before there are numerous ways to determine the
IP - but be aware that power outages and other circumstances can change the IP 
address of your Pi. For that reason it is advisable to give it a static IP 
address on your network - which you can do by configuring the wifi router or 
asking your local tech support for help.

When accessing the admin the username/password will be the credentials you 
setup when you ran install.sh.

Upload a wave file by adding a wave. There is no progress indicator on the wave
file upload interface - so be patient and wait for the page to refresh before 
navigating.

Scheduling is done per-day-of-the-week. Only one contiguous block of time per
day can be scheduled. To schedule a playback, create a playlist from one or
more wave files. The playlist will loop until the scheduled time ends, and the
currently playing wave file will be allowed to finish before the audio
terminates after the end time is reached.

The configured schedule will always be honored unless you add a Manual Override.
Manual Overrides can be scheduled for specific dates into the future and may
start or stop playlists. Volume control and play/stop functions can be accessed
from the main page: `http://<hostname>/`

## For Developers

This software uses the [Django](https://www.djangoproject.com/) webserver to 
provide the user interface.

The [Poetry](https://python-poetry.org/) build tool is used to manage 
dependencies and build the project:

You may also want to install [pyaudio](https://pypi.org/project/PyAudio/) for 
audio support on OSX.

`poetry install -E all`

Run the tests:
`poetry run ./etc_player/player.py test`

Run the development server:
   * `poetry run ./etc_player/player.py migrate`
   * `poetry run ./etc_player/player.py runserver`

The operational environment is configured using scripts located in 
etc_player/ops. ``install.sh`` can be referenced to see how they are installed 
onto the system. The architecture serves the Django web interface using 
gunicorn proxied through nginx. The audio player script is managed as a simple 
always-on systemd service which makes the audio playback robust to power 
interruptions and other system failures.
