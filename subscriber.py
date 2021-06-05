#!/usr/bin/python3
from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import Tuple
from time import sleep
import sqlite3
import json
import schedule

# Base URL for the nexushub API
API = 'https://api.nexushub.co/wow-classic/v1'
# The server/faction market to pull data for
AH = 'pagle-alliance'

class Subscriber:
    def __init__(self, API: str, auction_house: str, database='ah.db'):
        '''
            API:            string,
                            base url of API to pull data from
            auction_house:  string,
                            auction houseto pull data for, example: 'faerlina-alliance'
            scan_id:        integer,
                            unique id of the current market scan available on the API
            scanned_at:     string,
                            time of current market scan available on the API
        '''
        self.API = API
        self.auction_house = auction_house
        self.database = database
        self.scan_id = 0
        self.scanned_at = ""

        retry_strategy = Retry(
            # Configure an HTTPAdapter to retry/backoff
            # when a network connection is unavailable (IP lease renewal etc)
            # https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/#retry_on_failure
            total=10,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.http = Session()
        self.http.mount("https://", adapter)
        self.http.mount("http://",  adapter)

    def latest(self):
        ''' [GET] Gets info on the the latest scan available
            on the API for this auction house '''

        # Make GET request
        r = self.http.get(self.API + "/scans/latest/" + self.auction_house)

        # Validate json response
        try:
            r_json = json.loads(r.text)
        except json.JSONDecodeError as e:
            print("JSONDecodeError: {}".format(e))
            return

        try:
            if r_json['scanId'] != self.scan_id:
                # New scan_id indicates new data available
                print("[latest]:", str(r_json['scanId']), r_json['scannedAt'])
                # Update state to reflect this
                self.scan_id = r_json['scanId']
                s = r_json['scannedAt']

                # Update scanned_at state
                self.scanned_at = s
        except(KeyError):
            print(r_json['error'], r_json['reason'])
            return

    def overview(self):
        ''' [GET] Retrieves a full overview (aggregated info
            about all active auctions) of the auction house
            and saves it to disk in ./data/overview/ '''

        # Make GET request
        r = self.http.get(self.API + "/items/" + self.auction_house)

        # Load string JSON response into a dict
        resp_dict = json.loads(r.text)

        # Slug index contains WoW server name/faction pair
        # ("faerlina-alliance")
        slug = resp_dict['slug']

        print("[overview/INSERT]: retrieved new overview from scan_id",
            str(self.scan_id))

        # Get a connection to the DB
        conn = sqlite3.connect(self.database)
        # Get a cursor
        c = conn.cursor()

        # For every anonymous dict in the parent dict
        for item in resp_dict["data"]:
            # Build a tuple of the data we want in left-to-right order
            # (or as the columns are ordered in the table)
            t = (
                self.scanned_at,
                self.scan_id,
                int(item['itemId']),
                item['marketValue'],
                item['historicalValue'],
                item['minBuyout'],
                item['numAuctions'],
                item['quantity'],
                slug
            )
            # Construct an INSERT query into the overview table
            sql = "INSERT INTO overview VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            # Execute the query, supplying the tuple containing the data
            try:
                c.execute(sql, t)
            except Exception as e:
                print("{}: {}".format(type(e), e))

        # After all item's data have been inserted, commit our changes 
        conn.commit()
        # Finally, close the connection.
        conn.close()

def main():
    # Create a new subscriber instance
    subscriber = Subscriber(API, AH)

    while True:
        last_scan_id = subscriber.scan_id
        last_scanned_at = subscriber.scanned_at

        # Retrieve information about the latest/current data available on the API
        subscriber.latest()

        # If there's new data available (scan id and time changed), retrieve it
        # Else do nothing (wait for new data)
        if last_scan_id != subscriber.scan_id\
        and last_scanned_at != subscriber.scanned_at:
            subscriber.overview()

        # Wait one minute
        sleep(60)

if __name__ == '__main__':
    main()
    
