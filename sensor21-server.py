#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import json
import logging
import yaml
import os
import subprocess

from flask import Flask

from two1.wallet.two1_wallet import Wallet
from two1.bitserv.flask import Payment

import sqldb as db

app = Flask(__name__)

# setup wallet
wallet = Wallet()
payment = Payment(app, wallet)

# hide logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# sqldb setup
latest_measurement = db.Operate()


@app.route('/manifest')
def docs():
    """
    Provides the manifest.json file for the 21 endpoint crawler.
    """
    with open('./manifest.yaml', 'r') as f:
        manifest = yaml.load(f)
    return json.dumps(manifest)


@app.route('/server_status')
def server_status():
    """
    Check the latest DB entry. If time is greater than 5 minutes
    since last update, server status is down. Returns number of
    seconds since last sensor update. Else server status returns
    up. Returns number of seconds since last sensor update. 
    """
    latest_measurement.read()
    timestamp = latest_measurement.barometer_package[0]['timestamp']
    time_str = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
    time_diff = datetime.datetime.now() - time_str
    response = 'Server is %s. Last measurement was made %f seconds ago.'
    if time_diff.seconds > 300:
        return response % ('down', time_diff.seconds)
    return response % ('up', time_diff.seconds)


@app.route('/')
@payment.required(5)
def measurement():
    return latest_measurement.read()

if __name__ == "__main__":
    import click

    @click.command()
    @click.option("-d", "--daemon", default=False, is_flag=True,
                  help="Run in daemon mode.")
    def run(daemon):
        if daemon:
            pid_file = './sensor21.pid'
            if os.path.isfile(pid_file):
                pid = int(open(pid_file).read())
                os.remove(pid_file)
                try:
                    p = psutil.Process(pid)
                    p.terminate()
                except:
                    pass
            try:
                p = subprocess.Popen(['python3', 'sensor21-server.py'])
                open(pid_file, 'w').write(str(p.pid))
            except subprocess.CalledProcessError:
                raise ValueError("error starting sensor21-server.py daemon")
        else:
            print("Server running...")
            app.run(host='0.0.0.0', port=5002)

    run()
