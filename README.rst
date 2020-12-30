ircbuilder
==========

This package provides a python api for sending commands to a Minetest server over IRC.

`The source for this package is available here <https://github.com/timcu/irc_builder>`_.

To install 

pip install ircbuilder

Requires Minetest with irc_builder mod

On Ubuntu or Debian linux::

  sudo apt install minetest lua-socket
  mkdir -p ~/.minetest/mods
  cd ~/.minetest/mods
  git clone --recursive git@github.com/minetest-mods/irc.git
  git clone git@github.com:ShadowNinja/minetest-irc_commands.git irc_commands
  git clone https://gitlab.com/VanessaE/basic_materials.git
  git clone https://gitlab.com/VanessaE/signs_lib.git
  git clone git@github.com:timcu/irc_builder.git
  minetest

On Windows::

  # Download and extract minetest-5.3.0-win64.zip to Documents folder (https://www.minetest.net/downloads/)
  # Run Git-Bash (you will need to install it first. https://git-scm.com/download/)
  cd ~/Documents/minetest/mods
  git clone --recursive git@github.com/minetest-mods/irc.git
  git clone git@github.com:ShadowNinja/minetest-irc_commands.git irc_commands
  git clone https://gitlab.com/VanessaE/basic_materials.git
  git clone https://gitlab.com/VanessaE/signs_lib.git
  git clone git@github.com:timcu/irc_builder.git
  exit
  # Double click on Documents > minetest > bin > minetest.exe

On Mac OS X::

  brew install minetest luarocks-5.1
  luarocks-5.1 install luasocket
  mkdir -p ~/Library/Application\ Support/minetest/mods
  cd ~/Library/Application\ Support/minetest/mods
  git clone --recursive git@github.com/minetest-mods/irc.git
  git clone git@github.com:ShadowNinja/minetest-irc_commands.git irc_commands
  git clone https://gitlab.com/VanessaE/basic_materials.git
  git clone https://gitlab.com/VanessaE/signs_lib.git
  git clone git@github.com:timcu/irc_builder.git
  /usr/local/opt/minetest/minetest.app/Contents/MacOS/minetest

On Mac OS X using MacPorts::

  sudo port install minetest luarocks
  sudo -H luarocks install luasocket
  cd /opt/local/share/lua/5.1
  sudo ln -s ../5.3/socket
  # Then continue from third line above

Once running, adjust the following settings::

  # Settings > Advanced > Server/Singleplayer > Security > Trusted mods > irc
  # Settings > Advanced > Mods > irc > Basic > Bot nickname > eg mtserver
  # Settings > Advanced > Mods > irc > Basic > IRC server > eg irc.undernet.org
  # Settings > Advanced > Mods > irc > Basic > IRC server port > eg 6667
  # Settings > Advanced > Mods > irc > Basic > Channel to join > eg ##myminetest


