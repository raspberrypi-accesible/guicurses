# -*- coding: utf-8 -*-
""" Module with some useful utilities, not related to GUI."""
import shutil

def get_disk_usage(value=2):
	""" Gets disk usage in bites. 0 = total, 1 = used, 2 = free."""
	return shutil.disk_usage("/")[value]

def convert_bites(number_of_bites, convert_to="gb"):
	n = 1
	if convert_to == "kb":
		n = 1<<10
	if convert_to == "mb":
		n = 1<<20
	elif convert_to == "gb":
		n = 1<<30
	if number_of_bites != 0 and n != 1:
		return number_of_bites/n

def get_temperature():
	""" Retrieves current temperature for CPU in a raspberry pi.
	Didn't tried this in other SoC's"""
	return int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1e3