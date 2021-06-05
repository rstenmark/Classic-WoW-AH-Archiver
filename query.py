from typing import Tuple
from csv import reader
from json import loads
import pandas as pd
import sqlite3

def get_item_id_for_item_name(item_name: str) -> Tuple:
    """ Returns a tuple containing the integer item ID
        and the string item name for a given item name.

    Keyword arguments:
    item_name -- A string WoW Classic item name.
    """

    with open("items.csv", 'r+') as f:
        # new csv.reader instance
        r = reader(f, delimiter=',')

        # Lookup item id for given item name
        for line in r:
            if line[1].lower() == item_name.lower():
                # line[0] contains the item id
                # line[1] contains the item name
                return (int(line[0]), line[1])

    # If there wasn't an item with the given name, raise IndexError
    raise IndexError("No item ID for the given item name could be found")

def get_historical_df(item_name: str) -> pd.DataFrame:
    item_id = None
    ret = pd.DataFrame()

    item_id, item_name = get_item_id_for_item_name(item_name)

    # Get a connection to the DB
    conn = sqlite3.connect("ah.db")
    # Get a cursor
    c = conn.cursor() 
    # Construct the query
    sql = "SELECT * FROM overview WHERE item_id = (?)"
    try:
        c.execute(sql, (str(item_id), ))
    except Exception as e:
        print(e)

    data = c.fetchall()
    ret = pd.DataFrame(data,
        columns=['date', 'scan_id', 'item_id', 'market_value', 
        'historical_value', 'min_buyout', 'num_auctions', 'quantity', 'slug']
    )

    conn.commit()
    conn.close()

    return ret
