import os
import sys
import datetime
from whoosh.fields import Schema, TEXT, STORED, KEYWORD, DATETIME, ID
from whoosh.index import create_in, open_dir, exists_in
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.query import Query, Term
from whoosh.analysis import NgramTokenizer
from Engine import Engine


INDEX_DIRECTORY = '/home/koopuluri/index_directory'
engine = Engine(INDEX_DIRECTORY, fresh=False)

results = engine.query('ab')
print "Number Hits: ", len(results)

