import argparse
import os
from whoosh.fields import Schema, TEXT, STORED, KEYWORD, DATETIME, ID
from whoosh.analysis import NgramTokenizer
from whoosh.index import create_in, open_dir, exists_in
import shutil

FILENAME_SCHEMA = Schema(path = ID(stored=True),
							 mod_time = DATETIME(stored=True),
							 content = TEXT(stored=True, analyzer=NgramTokenizer(minsize=2, maxsize=15))
							 )



parser = argparse.ArgumentParser(description="the index directory")
parser.add_argument("index_directory", help="the index_directory to refresh")
args = parser.parse_args()
index_directory = args.index_directory



if os.path.exists(index_directory):
	shutil.rmtree(index_directory)

os.mkdir(index_directory)
ix = create_in(index_directory, FILENAME_SCHEMA)
