#!/usr/bin/env python3

# Monitor current applied to PEM cell, and determine charge (cumulative current)
#
# Setup: Raspberry Pi connected to Adafruit 1085 board (4-channel ADC, 16 bit)
# - Use Hall sensor to determine the cell current (ACS712, 10A version). Sensor output is a voltage signal.
# - Use ADC to read Hall sensor signal (Pin 0 on Adafruit 1085)
# - Convert the Hall sensor voltage from the ADC reading to cell current

# See https://circuitpython.readthedocs.io/projects/ads1x15/en/latest/

import argparse
import datetime
import time
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


##############################
# parsing of input arguments #
##############################
parser = argparse.ArgumentParser(description='Monitor current through PEM 3H enrichment cells and determine cumulative charge.')
parser.add_argument('--datafile', nargs='?', help='data file (name/path)')
args = parser.parse_args()
if args.datafile is not None:
	f = open(args.datafile,'w')
	print('Saving output to file ' + args.datafile + '...')
else:
	f = None


####################
# helper functions #
####################

def printit(text,f=''):
	# print date/time followed by text either to stdout (if f is empty) or to file (if f is not empty)

	# prepend date/time:
	now = datetime.datetime.now()
	text = now.strftime("%Y-%m-%d %H:%M:%S") + '\t' + text

	#print text:
	if f:
		print(text,file=f)
		f.flush()
	else:
		print(text)
	return


################
# Main program #
################


# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1015(i2c)

# Create single-ended input on pin 0 of ADC (Hall sensor for cell current):
hall = AnalogIn(ads, ADS.P0)

# Parameters to convert ADC voltage to current flowing thogh Hall sensor:
# current is I = A x (U-U0), where A is a conversion factor, U is the voltage at the Hall sensor output, and U0 is the 'zero' signal at current I = 0.0 A
U0 = 2.605	# 'zero' voltage 
A  = -9.615	# conversion factor

t0 = time.time();

# number of readings per averageing step:
N = 1000

# total charge ('Ampere-hours'), in Coulomb:
Q = 0.0

# Say hello:
printit('Monitoring cell current and total charge',f)

# Read Hall sensor, determine current and charge:
while True:
	
	# determine mean Hall sensor output (voltage):
	UH = 0.0
	t1 = time.time()
	for i in range(N):
		UH = UH + hall.voltage # voltage at ADC pin-0 (Hall sensor)
	t2 = time.time()

	UH = UH/N

	# convert mean Hall sensor voltage to current:
	IC = A*(UH-U0)
	
	# cumulative current (charge):
	Q = Q + IC*(t2-t1)

	# show data:
	printit("{:>.1f}...{:>.1f} s:\t I = {:>.2f} A\t Q = {:>.2E} C".format(t1-t0 , t2-t0 , IC , Q),f)
