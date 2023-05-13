# etc_design_player

Use [Raspberry Pi](https://www.raspberrypi.com/) to play audio wave files on a 
configurable schedule or on demand via a web interface. This software was 
originally developed to time the audio playback of museum exhibit audio tracks
with the opening schedule of the museum.


## Installation

Install the Raspberry Pi operating system and connect it to your local network.
Determine the Raspberry Pi's IP address - [there are numerous ways to do this](https://letmegooglethat.com/?q=How+do+I+determine+my+Raspberry+PI%27s+IP+address%3F).
Replace 192.168.1.106 with the correct IP address for your raspberry pi below 
when following this procedure:

 - Download the [latest package](https://raw.githubusercontent.com/bckohan/etc_design_player/blob/main/etc_player.zip).
 - Install the package (via Raspberry PI Desktop):
    * Unzip the downloaded package.
    * Double click on the install.sh file and select "execute in terminal".
 - Install the package (via terminal, replace IP and "pi" with your raspberry 
   pi's IP address and username respectively). 
   [You will also need to enable ssh on your pi](https://letmegooglethat.com/?q=enable+ssh+on+raspberry+pi)
   
    * `scp ~/Downloads/etc_player.zip pi@192.168.1.106:./`
    * `ssh pi@192.168.1.106`
    * `pi@raspberrypi:~ $> gunzip ./etc_player.zip`
    * `pi@raspberrypi:~ $> cd ./etc_player`
    * `pi@raspberrypi:~ $> ./install.sh`
 - Follow all prompts.
 - Configure your playback: http://192.168.1.106/admin

## Usage



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
