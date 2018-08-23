# Created on:  08/10/2018
# Author  Amogh Kulkarni

from bitmex_websocket import BitMEXWebsocket
from database import DbClient
import pandas as pd
import os
import datetime
import psutil
import sys
from threading import Thread
import configparser
import time
import sys

configParser = configparser.ConfigParser()
configParser.read(os.curdir + r'\\resources\\config.ini')
dbClient = DbClient()

count = 0

while True:
    try:
        ws = BitMEXWebsocket(endpoint="wss://www.bitmex.com/realtimemd",
                             symbol="XBTUSD", api_key=None, api_secret=None)
        if ws is not None:
            break
    except KeyboardInterrupt:
        break
    except:
        print('Unable to connect to socket')
        count += 1
        if count > 10:
            break


def run():
    try:
        time.sleep(2)

        while True:

            count = 0

            while True:
                try:
                    instrument = ws.get_instrument()
                    if instrument is not None:
                        break
                except KeyboardInterrupt:
                    break
                except IndexError:
                    print('index out of range')
                    count += 1
                    if count > 10:
                        break

            df = pd.DataFrame(instrument, index=['exchange'])
            df['exchange'] = 'Bitmex'

            timestamp = df['timestamp'].tolist()[0]

            df['timestamp'] = datetime.datetime.strptime(
                timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")

            df = df.reset_index().set_index(['timestamp'])

            running_process = False

            for pid in psutil.pids():
                p = psutil.Process(pid)
                if p.name() == "influxd.exe":
                    running_process = True
                    break

            if running_process == False:
                os.execv(configParser['database']['influx_path'], sys.argv)

            df = dbClient.df_int_to_float(df)

            dbClient.save_to_db(df, measurement="bitmex_socket")
    except KeyboardInterrupt:
        sys.exit(0)


t = Thread(target=run, args=())
t.start()