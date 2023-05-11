sudo apt install nginx emacs python3-pyaudio alsa-tools alsa-utils
sudo mkdir /opt/player
sudo chown -R mvc:mvc /opt/player
python -m venv /opt/player
source /opt/player/bin/activate
pip3 install ~/etc_player-*.whl
echo "source /opt/player/bin/activate" >> ~/.bashrc
echo "export PLAYER_DIR=/var/www/player" >> ~/.bashrc
sudo mkdir /var/www/player
sudo chown -R mvc:mvc /var/www/player
export PLAYER_DIR=/var/www/player
sudo ln -s /opt/player/lib/python3.9/site-packages/etc_player/ops/player.nginx /etc/nginx/sites-available/player
sudo ln -s /etc/nginx/sites-available/player /etc/nginx/sites-enabled/player
sudo rm /etc/nginx/sites-enabled/default
sudo rm /etc/nginx/sites-available/default
sudo ln -s /opt/player/lib/python3.9/site-packages/etc_player/ops/player.service /etc/systemd/system/player.service
sudo ln -s /opt/player/lib/python3.9/site-packages/etc_player/ops/player.socket /etc/systemd/system/player.socket
sudo ln -s /opt/player/lib/python3.9/site-packages/etc_player/ops/audio.service /etc/systemd/system/audio.service
sudo ln -s /opt/player/lib/python3.9/site-packages/etc_player/ops/audio.socket /etc/systemd/system/audio.socket
player migrate
player collectstatic
player createsuperuser --email noreply@localhost
sudo systemctl daemon-reload
sudo systemctl enable player
sudo systemctl start player
sudo systemctl enable audio
sudo systemctl start audio
sudo systemctl restart nginx
