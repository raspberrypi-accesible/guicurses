#!/bin/bash
#please, run this script as root
#make directories
mkdir -p guicurses_0.5/usr/lib/python3/dist-packages/guicurses
mkdir -p guicurses_0.5/usr/share/doc/guicurses
#copy files
cp guicurses/__init__.py guicurses/widgets.py guicurses/window.py guicurses_0.5/usr/lib/python3/dist-packages/guicurses
cp copyright guicurses/usr/share/doc/guicurses
cp changelog.Debian guicurses_0.5/usr/share/doc/guicurses
gzip -9 guicurses_0.5/usr/share/doc/guicurses
chown -R root.root guicurses_0.5
chmod -R 755 guicurses_0.5
chmod 644 guicurses_0.5/DEBIAN/control
chmod +x guicurses_0.5/usr/lib/python3/dist-packages/guicurses/__init__.py
chmod +x guicurses_0.5/usr/lib/python3/dist-packages/guicurses/widgets.py
chmod +x guicurses_0.5/usr/lib/python3/dist-packages/guicurses/window.py
#build the package
dpkg-deb --build guicurses_0.5
