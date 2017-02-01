#!/bin/bash

# sensor21 install script

# Print program warning + text coloring
print_warning() {
    printf "\e[1;33m$1\e[0m\n"
}

# Print program good response + text coloring
print_good() {
    printf "\e[1;32m$1\e[0m\n"
}

### Main program execution
print_good "Welcome to sensor21 installer!"

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

print_warning "Input your country abbreviation and hit enter. Example: USA or CA"
read -p "Country: " USER_COUNTRY
sed -i 's|'"{COUNTRY}"'|'"$USER_COUNTRY"'|g' manifest.yaml
echo ""

## Set up 21 account
print_good "The manifest.yaml has been updated, thank you."
