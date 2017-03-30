#!/bin/bash
#please, run this script as root
#make directories
mkdir -p debian/usr/lib/python3.4/dist-packages/guicurses
#copy files
cp guicurses/__init__.py guicurses/widgets.py guicurses/window.py guicurses_0.5/usr/lib/python3.4/dist-packages/guicurses
chown -R root.root guicurses_0.5
chmod -R 755 guicurses_0.5
chmod 644 guicurses_0.5/DEBIAN/control
#build the package
dpkg-deb --build guicurses_0.5
