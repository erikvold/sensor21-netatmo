#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import json
import mpl3115a2 as mpl
import sqlite3
import sys
import os

DATABASE_FILE = "{PWD}"


class BarometerSQL():

    """
    Interface `measurements.db` and `mpl3115a2.py`.

    Install SQLite3, then run:
    $ sqlite3 measurements.db

    Set up database tables.
    $ python3
    > import db
    > a = BarometerSQL()
    > a.create_table()
    > a.close_connection
    """

    def __init__(self):
        """
        Connects to barometer.db and sets up an sql cursor.
        """
        self.conn = sqlite3.connect(DATABASE_FILE)
        self.cursor = self.conn.cursor()

    def create_table(self):
        """
        Creates default table for logging barometer sensor output.
        """
        query = 'CREATE TABLE Barometer(Id INTEGER PRIMARY KEY AUTOINCREMENT, Datetime TEXT, Temperature REAL, Pressure REAL)'
        self.cursor.execute(query)

    def get_values(self):
        """
        Pulls current values from bitsense instance.
        """
        self.barometer = mpl.PressureAPI({I2C_TYPE})
        date = str(datetime.datetime.now())
        temperature = self.barometer.get_temperature()
        pressure = self.barometer.get_pressure()
        self.barometer.close()
        return [date, temperature, pressure]

    def write_values(self, inputs):
        """
        Insert inputs list into barometer.db.
        """
        query = 'INSERT INTO Barometer(Datetime, Temperature, Pressure) VALUES(?,?,?)'
        self.cursor.execute(query, (inputs))
        self.conn.commit()

    def read_latest(self, index_height=1):
        """
        Gets the index_height most recent entries in barometer.db.
        """
        query = 'SELECT * FROM Barometer ORDER BY Id DESC LIMIT (?);'
        res = self.cursor.execute(query, (index_height,))
        return res.fetchall()

    def close_connection(self):
        """
        Close the sqlite3 handle.
        """
        self.conn.close()


class Operate():

    """
    Operator class that calls an instance of AltitudeSQL
    to update the db and read from it.
    """

    def update_table(self):
        """
        Grab the latest values from the barometer and
        committo barometer.db.
        """
        self.handle = BarometerSQL()
        self.reading = self.handle.get_values()
        self.handle.write_values(self.reading)
        self.handle.close_connection()
        return self.reading

    def read(self, index_height=1):
        """
        Grabs readings from barometer.db.
        """
        self.handle = BarometerSQL()
        self.output = self.handle.read_latest(index_height)
        self.handle.close_connection()
        self.barometer_package = []
        for x in range(0, index_height):
            self.barometer_package.append({
                'timestamp': self.output[x][1],
                'temperature': self.output[x][2],
                'pressure': self.output[x][3]
            })
        return json.dumps(self.barometer_package)


def main():
    db_is_new = os.path.exists(DATABASE_FILE)
    db_setup = BarometerSQL()
    if db_is_new is False:
        db_setup.create_table()
        db_setup.close_connection()
    values = Operate()
    values.update_table()
    print('%s %s\n%s' % (
        'Database created, schema written, and first reading taken.',
        'You should see sensor data printed now.',
        values.read()))

if __name__ == "__main__":
    main()
