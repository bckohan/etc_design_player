# etc_design_player

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI version](https://badge.fury.io/py/etc-player.svg)](https://pypi.python.org/pypi/etc-player/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/etc-player.svg)](https://pypi.python.org/pypi/etc-player/)
[![PyPI djversions](https://img.shields.io/pypi/djversions/etc-player.svg)](https://pypi.org/project/etc-player/)
[![PyPI status](https://img.shields.io/pypi/status/etc-player.svg)](https://pypi.python.org/pypi/etc-player)
[![Code Cov](https://codecov.io/gh/bckohan/etc_design_player/branch/main/graph/badge.svg?token=0IZOKN2DYL)](https://codecov.io/gh/bckohan/etc_design_player)
[![Test Status](https://github.com/bckohan/etc_design_player/workflows/test/badge.svg)](https://github.com/bckohan/etc_design_player/actions/workflows/test.yml)
[![Lint Status](https://github.com/bckohan/etc_design_player/workflows/lint/badge.svg)](https://github.com/bckohan/etc_design_player/actions/workflows/lint.yml)


Use a [Raspberry Pi](https://www.raspberrypi.com/) to play audio wave files on a configurable schedule or on demand via a web interface. This software was originally developed to time the audio playback of museum exhibit audio tracks with the opening schedule of the museum.


## Installation

Install the Raspberry Pi operating system and connect it to your local network. **Change the hostname of your Raspberry Pi to a memorable unique name** - this name will be used access the scheduler later. The **hostname** can be changed by clicking the raspberry in the upper left menu and selecting "Preferences" -> "Raspberry Pi Configuration" -> "System" -> "**Hostname**". While you have the preferences open, also enable ssh access by selecting the "Interfaces" and toggling SSH on. Click save and reboot.

Most wifi networks will allow you to access your Raspberry Pi over the network using the **hostname** you set. Only if your network does not will you have to use its IP address instead. [There are numerous ways to do determine the IP](https://letmegooglethat.com/?q=How+do+I+determine+my+Raspberry+PI%27s+IP+address%3F) - but be aware that power outages and other circumstances can change the IP address of your Pi. For that reason it is advisable to give it a static IP address on your network - which you can do by configuring the wifi router or asking your local tech support for help.

 - To install from the Raspberry Pi Desktop:
    * Download the [installer](https://github.com/bckohan/etc_design_player/raw/main/install.sh).
    * Double click on the install.sh file and select "execute in terminal".
 - To install from your computer's terminal: (replace "**hostname**" and "pi" with your Pi's **hostname** and account username respectively). 

    ```console
      ssh pi@hostname
      ?> curl -sSL https://github.com/bckohan/etc_design_player/raw/main/install.sh | bash
    ```

 - After a few minutes the install script will prompt you to enter a username and password. This will be the account you use to login to the web interface to configure the playback. Once the install script disappears the install is complete.
 - To configure your playback from a computer on the same wifi network you can access from: `http://hostname/admin` where **hostname** is the **hostname** you set earlier or if on your Raspberry Pi's desktop you may also use http://localhost/admin

## Usage

Most wifi networks will allow you to access the scheduler interface through `http://hostname/admin` (where **hostname** is the **hostname** you set during install). If this does not work you may need to use the IP  address instead. As mentioned before there are numerous ways to determine the IP.

When accessing the admin the username/password will be the credentials you setup when you ran install.sh.

Upload a wave file by adding a wave. There is no progress indicator on the wave file upload interface - so be patient and wait for the page to refresh before navigating after you hit save.

Scheduling is done per-day-of-the-week. Only one contiguous block of time per day can be scheduled. To schedule a playback, create a playlist from one or more wave files. The playlist will loop until the scheduled time ends, and the currently playing wave file will be allowed to finish before the audio terminates after the end time is reached.

The configured schedule will always be honored unless you add a Manual Override. Manual Overrides can be scheduled for specific dates into the future and may start or stop playlists. Volume control and play/stop functions can be accessed from the main page: `http://hostname/`

**_NOTE:_**  On some hosts (OSX) you may need to use `hostname.local` instead of `hostname`.

## For Developers

This software uses the [Django](https://www.djangoproject.com/) webserver to provide the user interface.

The [Poetry](https://python-poetry.org/) build tool is used to manage dependencies and build the project:

You may also want to install [pyaudio](https://pypi.org/project/PyAudio/) for audio support on OSX.

`poetry install -E all`

Run the tests:
`poetry run ./etc_player/player.py test`

Run the development server:
   * `poetry run ./etc_player/player.py migrate`
   * `poetry run ./etc_player/player.py runserver`

The operational environment is configured using scripts located in etc_player/ops. ``install.sh`` can be referenced to see how they are installed onto the system. The architecture serves the Django web interface using gunicorn proxied through nginx. The audio player script is managed as a simple always-on systemd service which makes the audio playback robust to power interruptions and other system failures.
