import os
import sys
import datetime
from Engine import Engine
from whoosh.fields import Schema, TEXT, STORED, KEYWORD, DATETIME, ID
from whoosh.index import create_in, open_dir, exists_in
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.query import Query, Term
from whoosh.analysis import NgramTokenizer



index_directory = '/home/koopuluri/index_directory'
exists = exists_in(index_directory)
print "index directory exists: ", exists
engine = Engine(index_directory)

added, deleted = engine.incremental_index('/home/koopuluri/testFS')

print "files added: ", added
print "files deleted: ", deleted

with engine.ix.searcher() as searcher:
	for fields in searcher.all_stored_fields():
		print "path: ", fields["path"]

