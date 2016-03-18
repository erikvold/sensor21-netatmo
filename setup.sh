#!/bin/bash

# sensor21 install script
#
# This script will help install dependencies for sensor21. It also
# sets up the SQLite database to abstract the low level hardware 
# communications from server requests to eliminate bus collisions. 

### List of packages to install
declare -a APT_PACKAGES=("unzip" "python3-pip" "sqlite3")
declare -a PIP3_PACKAGES=("flask" "click" "python-periphery")
PACKAGE_PIGPIO="/usr/local/bin/pigpiod"

# Helper functions: bash pretty printing, pip3 and apt-get package
# installers / uninstallers

# Pretty print helper functions
# Print program step + text coloring
print_step() {
    printf "\n\e[1;35m $1\e[0m\n"
}

# Print program error + text coloring
print_error() {
    printf "\n\e[1;31mError: $1\e[0m\n"
}

# Print program warning + text coloring
print_warning() {
    printf "\e[1;33m$1\e[0m\n"
}

# Print program good response + text coloring
print_good() {
    printf "\e[1;32m$1\e[0m\n"
}

# Program installation functions
# Check to see if a program exists on the local machine
program_exists() {
    if ! type "$1" > /dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# Check to see if a pip3 package exists
pip_package_exists() {
	python3 -c "import $1" 2> /dev/null && return 0 || return 1
}

# Install apt packages
apt_installer() {
	if ! program_exists $1; then
		print_warning "Installing $1."
		sudo apt-get --force-yes --yes install $1
	else
		print_good "$1 installed."
	fi
}

# Install pip3 modules
pip3_installer() {
	# fix for python-periphery pip3 install vs package name
	if [ "$1" = "python-periphery" ]; then
		var="periphery"
		if ! pip_package_exists $var; then
			print_warning "Installing $1."
			sudo pip3 install $1
		else
			print_good "$1 installed."
		fi
	else
		if ! pip_package_exists $1; then
			print_warning "Installing $1."
			sudo pip3 install $1
		else
			print_good "$1 installed."
		fi
	fi
}

### Main program execution
print_good "Welcome to sensor21 installer!"

UNAME=$(uname)
case "${UNAME:-nil}" in
	Linux|LINUX) ##pass 
	;;
    Darwin) ## Mac OSX
        print_error "Sorry, $UNAME is not supported. Sensor21 is designed for Raspberry Pi based systems."
        exit 1
    ;;
    *)
        print_error "Sorry, $UNAME is not supported. Sensor21 is designed for Raspberry Pi based systems."
        exit 1
    ;;
esac

BC_FLAG=0

# BC-specific
if [ "$(cat /proc/device-tree/hat/product 2>/dev/null)" = "21 Bitcoin Computer" ]; then
	BC_FLAG=1
	print_good "21 Bitcoin Computer detected. Defaulting to software I2C."
	sed -i 's|'"{I2C_TYPE}"'|'1'|g' sqldb.py
else
	print_good "Raspberry Pi detected. Defaulting to hardware I2C."
	sed -i 's|'"{I2C_TYPE}"'|'0'|g' sqldb.py
	print_good "Deploying HW I2C repeated start fix for RPi."
	echo -n 1 | sudo tee -a /sys/module/i2c_bcm2708/parameters/combined
fi
echo ""

## Overwrite path with present working directory.
print_warning "Gathering present working directory for sensor21."
print_warning "If you move sensor21 to another folder, you must manually edit sqldb.py and cron.txt and update paths to your present working directory."

FULL_PATH="$(pwd)"
DB_PATH="$FULL_PATH/measurements.db"
sed -i 's|'"{PWD}"'|'"$DB_PATH"'|g' sqldb.py
sed -i 's|'"{PWD}"'|'"$FULL_PATH"'|g' cron.txt

## Update apt-get package list
print_step "updating package list"
sudo apt-get update
echo ""

## Install prerequisites
print_step "checking/installing prerequisites"

# Loop through apt packages array and check if present, then install if not. 
for var in "${APT_PACKAGES[@]}"
do
	# fix for pip3 install vs package name
	if [ "$var" = "python3-pip" ]; then
		var="pip3"
	fi
	apt_installer $var
done

# Loop through pip3 packages array and check if present, then install if not. 
for var in "${PIP3_PACKAGES[@]}"
do
	pip3_installer $var
done

# Pull down PIGPIO library, make binary, and then install.
# PIGPIO enables software I2C communications on RPi GPIO pins 
if [ "$BC_FLAG" = "1" ]; then
	if ! program_exists $PACKAGE_PIGPIO; then
		print_warning "Installing PIGPIO."
		wget -N abyz.co.uk/rpi/pigpio/pigpio.zip 2>&1  | grep "not retrieving" 2>&1 > /dev/null || unzip pigpio.zip
		cd PIGPIO
		make
		sudo make install
		sudo pigpiod
		cd ~/sensor21
		sudo rm pigpio.zip
	else
		print_good "PIGPIO installed."
		sudo pigpiod
	fi
fi

print_good "Prerequisites installed."

## Initialize SQLite database and take first sensor21 reading.
print_step "Setting up SQLite Database..."
python3 sqldb.py

## Verify SQLite database insertion and reading.
print_step "Verifying SQLite Datbase write."
sqlite3 measurements.db "SELECT * FROM Barometer"
echo ""

## Prompt user to replace crontab file. cron.txt automatically grabs sensor data every minute. 
print_warning "Warning: If you have an existing crontab, the next command will overwrite it."
print_warning "If you are not familiar with crontab, choose Y."

read -n1 -p "Proceed? [y/n] " CRON_RESPONSE
case $CRON_RESPONSE in  
	y|Y) 	print_step " Editing crontab..."; crontab cron.txt;;
	*) echo " Crontab not updated. Please run crontab cron.txt to set up the cron job.";;
esac

## Success!!!
print_good "Install complete." 
print_good "Database created, schema written to the table, and sensor readings written to DB every 1 minute."
print_warning "Remove cron job with crontab -r."

echo ""

# Edit manifest file to include location information
print_warning "Editing manifest.yaml to include location-specific information."
print_warning "Input your city and hit enter. Example: San Francisco"
read -p "City: " USER_CITY
sed -i 's|'"{CITY}"'|'"$USER_CITY"'|g' manifest.yaml
echo ""
print_warning "Input your state abbreviation and hit enter. Example: CA"
read -p "State: " USER_STATE
sed -i 's|'"{STATE}"'|'"$USER_STATE"'|g' manifest.yaml
echo ""
print_warning "Input your country abbreviation and hit enter. Example: USA"
read -p "Country: " USER_COUNTRY
sed -i 's|'"{COUNTRY}"'|'"$USER_COUNTRY"'|g' manifest.yaml
echo ""

## Set up 21 account
print_good "Now running 21 status to verify user & wallet creation."
print_warning "If you have not signed up for an account yet, go to https://21.co/signup/"

21 status