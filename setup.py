import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "guicurses",
    version = "0.4",
    author = "Manuel Cortez",
    author_email = "manuel@manuelcortez.net",
    description = "A set of utilities for building accessible applications with curses",
    license = "GPL V2",
    keywords = "Gui curses accessibility speakup",
    url = "http://manuelcortez.net:1337/pi/guicurses",
    long_description=read('README'),
    packages = ["guicurses"],
)