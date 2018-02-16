ircbuilder
==========

This package provides a python api for sending commands to a Minetest server over IRC.

`The source for this package is available here <https://github.com/timcu/irc_builder>`_.

To install 

pip install ircbuilder

Requires Minetest with irc_builder mod

On Mac OS X::

  brew install minetest
  mkdir -p ~/Library/Application\ Support/minetest/mods
  cd ~/Library/Application\ Support/minetest/mods
  git clone --recursive git@github.com/minetest-mods/irc.git
  git clone git@github.com:ShadowNinja/minetest-irc_commands.git
  mv minetest-irc_commands irc_commands
  git clone git@github.com:minetest-mods/signs_lib.git
  git clone git@github.com:timcu/irc_builder.git
  /usr/local/opt/minetest/minetest.app/Contents/MacOS/minetest

On Ubuntu or Debian linux::

  sudo apt-get install minetest
  mkdir -p ~/.minetest/mods
  cd ~/.minetest/mods
  git clone --recursive git@github.com/minetest-mods/irc.git
  git clone git@github.com:ShadowNinja/minetest-irc_commands.git
  mv minetest-irc_commands irc_commands
  git clone git@github.com:minetest-mods/signs_lib.git
  git clone git@github.com:timcu/irc_builder.git
  minetest

On Windows::

  # Download and extract minetest-0.4.16-win64.zip to Documents folder
  # Run Git-Bash (you will need to install it first)
  cd ~/Documents/minetest/mods
  git clone --recursive git@github.com/minetest-mods/irc.git
  git clone git@github.com:ShadowNinja/minetest-irc_commands.git
  mv minetest-irc_commands irc_commands
  git clone git@github.com:minetest-mods/signs_lib.git
  git clone git@github.com:timcu/irc_builder.git
  exit
  # Double click on Documents > minetest > bin > minetest.exe

Once running, adjust the following settings::

  # Settings > Advanced > Server/Singleplayer > Security > Trusted mods > irc
  # Settings > Advanced > Mods > irc > Basic > Bot nickname > eg mtserver
  # Settings > Advanced > Mods > irc > Basic > IRC server > eg irc.undernet.org
  # Settings > Advanced > Mods > irc > Basic > IRC server port > eg 6667
  # Settings > Advanced > Mods > irc > Basic > Channel to join > eg ##myminetest


