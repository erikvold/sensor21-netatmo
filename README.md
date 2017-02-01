# How to run and publish: _**sensor21-netatmo**_

## Prerequisites

You will need:

* A 21 Bitcoin Computer, or a DIY Bitcoin Computer
* A Netatmo Weather Station (with Outdoor module)


## Software Setup

### Step 1: Install/update 21
Get the latest version of the 21 software. If you don't have 21 installed yet, run `curl https://21.co | sh`. Then, join the 21 marketplace network.

``` bash
# Install 21 if required
curl https://21.co | sh

# Run 21 update
21 update

# Join the `21market` network
21 join
```

### Step 2: Clone the repository and setup
Clone the sensor21 repository, and run the setup script. You will be asked for user input multiple times.

``` bash
cd ~/

# Install git to clone the Sensor21 code
sudo apt-get install git

# git clone the code
git clone https://github.com/erikvold/sensor21-netatmo.git

# run the setup script
cd sensor21-netatmo
sudo easy_install3 pip
sudo pip3 install -r requirements.txt
source setup.sh
```

### Step 3: Create config.json

Rename `config-example.json` to `config.json` and provide the necessary information.

### Step 4: Start your server and publish your endpoint

Start the server with the following:

``` bash
python3 sensor21-server.py -d
```

After the server is running, pubish your endpoint with the 21 publish command. Replace the name and email fields with your information.

``` bash
21 publish submit manifest.yaml -p 'name="Joe Smith" email="joe@example.com" price="5" host="AUTO" port="6012"'
```

### Step 4: Verify you are part of the aggregator pool

After a few minutes, you should be able to use `21 publish list`
to see the endpoint you just put up:

``` bash
21 publish list
```

You can also use the verify endpoint on the sensor21 aggregator. Load your zerotier ip address, and then query the enpoint to verify you are part of the pool.

``` bash
# grab your ZeroTier IP address and save it to shell variable ZT_IP
ZT_IP=$(ifconfig | grep -A2 zt | grep inet | sed 's|[^0-9. ]||g' | sed 's|[^ \t]*||' | awk 'NR==1{print $1}')

# verify your endpoint is part of the pool
curl https://mkt.21.co/21dotco/sensor21_aggregator/sensor21/verify?zt_ip=$ZT_IP
```

### Step 5: View transactions with 21 log

After your server has been online for ~30 minutes, you can start to see transaction logs from the aggregator in your 21 log. You can see your incomes from sensor21 by running 21 log.

``` bash
21 log
```

## Troubleshooting

If you have further support requests, please join the public 21 slack channel #developers [here](http://slack.21.co/).

