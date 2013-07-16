from engine import Engine 
import argparse

"""
indexing a whole directory as an event based indexer would.
"""

parser = argparse.ArgumentParser(description="the index directory")
parser.add_argument("index_directory", help="the index_directory to refresh")
args = parser.parse_args()
index_directory = args.index_directory
search_engine = Engine(index_directory)


