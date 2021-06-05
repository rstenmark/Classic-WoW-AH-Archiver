#!/usr/bin/python3
from glob import glob
import json
import sqlite3

def migrate():
        for fname in glob("/home/rstenmark/WoWNexusHubClient/data/overview/*.json"):
            with open(fname, 'r+') as fd:
                resp_dict = json.loads(fd.read())

                # Slug index contains WoW server name/faction pair
                # ("faerlina-alliance")
                slug = resp_dict['slug']

                # Get a connection to the DB
                conn = sqlite3.connect("ah.db")
                # Get a cursor
                c = conn.cursor()

                # For every anonymous dict in the parent dict
                for item in resp_dict["data"]:
                    # Build a tuple of the data we want in left-to-right order
                    # (or as the columns are ordered in the table)
                    #print(fname[57:67])
                    #print(resp_dict['scannedAt'])
                    t = (
                        resp_dict['scannedAt'],
                        fname[57:67],
                        int(item['itemId']),
                        item['marketValue'],
                        item['historicalValue'],
                        item['minBuyout'], 
                        item['numAuctions'],
                        item['quantity'],
                        slug
                    )
                    #print(t)
                    # Construct an INSERT query into the overview table
                    sql = "INSERT INTO overview VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    # Execute the query, supplying the tuple containing the data
                    try:
                        c.execute(sql, t)
                    except Exception as inst:
                        print(inst)
                # After all item's data have been inserted, commit our changes 
                conn.commit()
                # Finally, close the connection.
                conn.close()

migrate()
