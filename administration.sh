#!/bin/bash

# Sensor21: MPL3115A2 Breakout Board Administration Script
#
# This script provides a few useful functions for working with
# system processes related to the MPL3115A2 sensor21 implementation.
# Note: pigpiod is only used for software I2C (used with 21 Bitcoin Computer)

# Usage: bash administration.sh <function>
#   bash administration.sh start_server
#   bash administration.sh restart_pigpiod
# function list
#   start_pigpiod, stop_pigpiod, restart_pigpiod
#   start_server, stop_server, restart_server
#   start_cron_job, stop_cron_job

## Process names
PIGPIOD="pigpiod"
SERVER="sensor21-server.py"

## Helper functions
# Check to see if a process is running
# Returns 0 if yes, 1 if no
check_process () {
	pgrep -f $1 > /dev/null
	return $?
}

# Stop process
stop_process () {
	proc_num=$(ps aux | grep -v grep | pgrep -f $1)
	sudo kill $proc_num > /dev/null
}

## PIGPIOD management
# start pigpiod
start_pigpiod () {
	if ! check_process $PIGPIOD; then
		sudo pigpiod
	fi	
}

# stop pigpiod
stop_pigpiod () {
	if check_process $PIGPIOD; then
		stop_process $PIGPIOD
	fi
}

# restart pigpiod
restart_pigpiod () {
	stop_pigpiod
	start_pigpiod
}

## Server Management
# start server
start_server () {
	start_pigpiod
	if ! check_process $SERVER; then
		python3 sensor21-server.py &
	fi
}

# stop server
stop_server () {
	if check_process $SERVER; then
		stop_process $SERVER
	fi
}

# restart server
restart_server () {
	stop_server
	start_server
}

## Crontab management
# start cron job
start_cron_job () {
	crontab -l 2>&1 | grep '* * * * * /usr/bin/python3 /home/twenty/sensor21/cron.py >> /home/twenty/sensor21/cron_log.txt 2>&1' > /dev/null
	if [ "$?" = "1" ]; then
		crontab cron.txt
	fi
}

# stop cron job
stop_cron_job () {
	crontab -l 2>&1 | grep '* * * * * /usr/bin/python3 /home/twenty/sensor21/cron.py >> /home/twenty/sensor21/cron_log.txt 2>&1' > /dev/null
	if [ "$?" = "0" ]; then
		crontab -r
	fi
}

# Print available functions if user runs with no arguments.
if [ "$1" = "" ]; then
	echo "usage: source administration.sh <FUNCTION>"
	echo "Note: pigpiod is only used for software I2C (used on 21 Bitcoin Computer)"
	echo ""
	echo "Supported functions:"
	echo "start_pigpiod, stop_pigpiod, restart_pigpiod"
	echo "start_server, stop_server, restart_server" 
	echo "start_cron_job, stop_cron_job"
else
	# Run function calls from script arguments
	$@
fi