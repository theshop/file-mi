import os
import sys
import time
from datetime import datetime
import timeit
import Image
from whoosh.fields import Schema, TEXT, STORED, KEYWORD, DATETIME, ID
from whoosh.index import create_in, open_dir, exists_in
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.query import Query, Term

"""
This class allows querying of the index
"""

# Search based on only pathname
FILENAME_SCHEMA = Schema(path = ID(stored=True),
						 mod_time = DATETIME(stored=True),
						 content = TEXT(stored=True, analyzer=NgramTokenizer(minsize=2, maxsize=15))
						 )

class IndexReader:

	def __init__(self, index_directory, buffered_writer):

		self.index_directory = index_directory
		self.buffered_writer = buffered_writer
		self.ix = open_dir(index_directory)


	def query(self, query):

		t0 = time.time()
		qp = QueryParser("content", schema=self.schema)
		q = qp.parse(query)
		results_as_strings = []
		with self.ix.searcher() as searcher:

			results = searcher.search(q, limit=None)
			for hit in results:
				results_as_strings.append(hit['path'])

		t1 = time.time()
		return [results_as_strings, (t1 - t0)]

	def buffered_query(self, query):

		t0 = time.time()
		qp = QueryParser("content", schema=self.schema)
		q = qp.parse(query)
		results_as_strings = []
		
		searcher = self.buffered_writer.searcher()

		results = searcher.search(q, limit=None)
		for hit in results:
			results_as_strings.append(hit['path'])

		t1 = time.time()
		return [results_as_strings, (t1 - t0)]

