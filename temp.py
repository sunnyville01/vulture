import os
import json
import time
import sqlite3
import requests
from os import path
import urllib.request


with open('coinex_markets.json', 'r') as myfile:
    coinex_markets_data=myfile.read()
coinex_markets = json.loads(coinex_markets_data)

with open('markets.json', 'r') as myfile:
    markets_data=myfile.read()
markets = json.loads(markets_data)


print(len(coinex_markets))
print(len(markets))
