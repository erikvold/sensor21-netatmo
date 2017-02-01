#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import yaml
import os
import subprocess

from flask import Flask

from two1.wallet.two1_wallet import Wallet
from two1.bitserv.flask import Payment

import netatmo

app = Flask(__name__)

# setup wallet
wallet = Wallet()
payment = Payment(app, wallet)

# hide logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

latest_measurement  = netatmo.Netatmo

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
    diff = latest_measurement.lastupdate()
    response = 'Server is %s. Last measurement was made %f seconds ago.'
    if diff > 700:
        return response % ('down', diff)
    return response % ('up', diff)

@app.route('/')
@payment.required(5)
def measurement():
    return json.dumps(latest_measurement.data())

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
            app.run(host='::', port=6012)

    run()
