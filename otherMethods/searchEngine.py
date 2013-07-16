"06/07/2013"
"""
- This class is used to create, maintain, and update the index directory used to store the indeces for the documents to search against. 
- For this version, only document names (paths) can be queried, but not the text within (will be added later to see difference in speed)
- The methods provided are:
-> initialize the Engine with directory: if exists, it will be used as it is/ it will be created
-> 
"""

"""
important note about the ix.writer():
opening the writer locks the index for writing, so opening another writer while one is already open will raise an exception (whoosh.store.LockError)
=> use whoosh.writing.AsyncWriter if you need to work around it.
- Opening a writer on the index does not prevent readers from opening and viewing the index
"""

import os
import sys
import time
from datetime import datetime
import random
import timeit
import Image
from whoosh.fields import Schema, TEXT, STORED, KEYWORD, DATETIME, ID
from whoosh.index import create_in, open_dir, exists_in
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.query import Query, Term
from whoosh.analysis import NgramTokenizer
from whoosh.writing import BufferedWriter, AsyncWriter

"""
This class will be used as the medium to interact with the search index directory.
Documents can be added to, removed from, and modified in the directory that stores all the document indeces (index_directory)
"""

class Engine:


	# Search based on only pathname
	FILENAME_SCHEMA = Schema(path = ID(stored=True),
							 mod_time = DATETIME(stored=True),
							 content = TEXT(stored=True, analyzer=NgramTokenizer(minsize=2, maxsize=15))
							 )

	IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg']

	"""
	initializes the engine with:
	- index_directory: where the indeces will be stored
	- fresh = False: set to True if engine should wipe out existing index_directory and start fresh
	- schema: set to FULLTEXT_SCHEMA if a full text search is required. Note that engine will automatically wipe out existing 
	index_directory to account for change in schema
	"""

	def __init__(self, index_directory, fresh = False, schema = FILENAME_SCHEMA):
		self.index_directory = index_directory
		self.schema = schema
		self.ix = None 
		self.error_log = '/home/labuser/Code/FileIndexer/error_log.txt'
	
		if not os.path.exists(index_directory):
			os.mkdir(index_directory)
			self.ix = create_in(index_directory, self.schema)
		else:
			if fresh:
				self.ix = create_in(index_directory, self.schema)
			else:
				self.ix = open_dir(index_directory)

		self.buffered_writer = None

	"""
	delete all currently stored indeces, and index contents of 'directory_path'
	"""

	def re_index(self, directory_path):

		#first clearing the existing index in the "indexDirectory" specified when Engine was initialized
		t0 = time.time()
		#writer = AsyncWriter(self.ix, writerargs={'procs':4, 'limitmb':128})
		#writer = self.ix.writer(procs=4, limitmb=128)
		writer = self.ix.writer(limitmb=512)
		print "writer is loaded"
		directoryExists = self.__add_directory(directory_path, writer)
		print "directory exists: ", directoryExists
		writer.commit()
		print "commited writer"
		t1 = time.time()
		return (t1 - t0)
		
	
	#goes to a directory and recursively indexes every DOCUMENT/FILE under it, but not directories under it 
    #returns a bool of whether the directory exists

	def __add_directory(self, directory_path, writer):

		if not os.path.isdir(directory_path):
			return False
		else:
			self.__add_path(directory_path, writer, 0)
			return True

	# recursive function that indexes an object if it is a file, else it traverses into that directory and continues

	def __add_path(self, path, writer, counter):

		if os.path.isfile(path):
			t0 = time.time()
			self.add_document(path, writer)
			t1 = time.time()
			time_taken = t1 - t0
			if random.choice(range(100)) < 10:
				print "time taken to index: ", [str(datetime.now()), path, time_taken]
		else:
			# This means that the path is to a directory, not a file

			print "not adding this path, it's a directory: ", [str(datetime.now()), path]
			ls = os.listdir(path)
			for i in ls:
				self.__add_path(os.path.join(path, i), writer, counter)

	"""
	indexes the filepath to the index_directory through the provided writer
	"""

	def add_document(self, filepath, writer):

		if not os.path.isfile(filepath):
			#print "not a file: ", filepath
			pass
		else:
			mtime = os.path.getmtime(filepath)
			try:
				writer.add_document(path = unicode(filepath), mod_time = datetime.fromtimestamp(mtime), content = unicode(filepath))
			except UnicodeDecodeError:
				print "The following gets unicode error: ", filepath
				f = open(self.error_log, 'w')
				f.write('UnicodeDecodeError: ' + filepath)
				f.close()

	"""
	removes the document with filepath as its ID. 
	return: number of documents deleted
	"""

	def remove_document(self, filepath, writer):

		removed = writer.delete_by_term("path", unicode(filepath))
		return removed

	"""
	removes documents matching query (as would be entered in search)
	return: number deleted
	"""

	def remove_by_query(self, query, writer):

		removed = writer.delete_by_query(query, searcher=None)
		return removed

	# used in incremental index to get all paths from the FS located at the dirname.

	def __my_docs(self, path):

		if os.path.isfile(path):
			return [path]
		elif 'DS_Store' in path:
			return []
		else:
			ls = os.listdir(path)
			out = []
			for i in ls:
				out.extend(self.__my_docs(os.path.join(path,i)))
			return out
	"""
	incrementally indexes the difference of the directory specified by dirname and the index stored at and for the dirname
	note: This is not the event based index, but will be used for testing purposes. 
	"""

	def incremental_index(self, dirname):

		files_added = 0
		files_deleted = 0
		ix = open_dir(self.index_directory)
		indexed_paths = set()
		to_index = set()

		with self.ix.searcher() as searcher:
			writer = ix.writer()

			for fields in searcher.all_stored_fields():
				indexed_path = fields['path']
				indexed_paths.add(indexed_path)

				if not os.path.exists(indexed_path):
					# Thise path was deleted since the last index
					writer.delete_by_term('path', indexed_path)
					files_deleted += 1

				else:
					# Checking if file was modified since last index:
					indexed_time = fields['mod_time']
					if datetime.fromtimestamp(os.path.getmtime(indexed_path)) > indexed_time:
						# file has been modified, delete and reindex
						writer.delete_by_term('path', indexed_path)
						files_deleted += 1
						to_index.add(indexed_path)

			# loop over all files in file system
			for path in self.__my_docs(dirname):
				if path in to_index or path not in indexed_paths:
					self.add_document(path, writer)
					files_added += 1
					

			writer.commit()
		return [files_added, files_deleted]
	"""
	takes in a query and returns the hits from the indeces.
	return: results as list of strings, time for query
	"""

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
	
	"""
	A fresh index of everything from directory to the index_directory
	"""

	def timed_index(self, directory):

		def test():
			self.re_index(directory)

		time = min(timeit.Timer(test).repeat(7, 1))
		return time

	"""
	returns an async writer for the index_directory
	"""

	def new_buffered_writer(self, period, limit, writer_limitmb):

		self.buffered_writer = BufferedWriter(self.ix, period=period, limit=limit, writerargs={'limitmb' : writer_limitmb})
		return self.buffered_writer

	def async_writer(self):

		return AsyncWriter(self.ix)

	
	"""
	# should this ever be used?
	def writer(self):

		return
	"""

"""
takes in a list of paths, and outputs the paths that are of images
"""

def filter_images(results_as_strings):

	image_list = []
	for filepath in results_as_strings:
		try:
			im = Image.open(filepath)
			chars = list(filepath)
			for i in range(len(chars)):
				if chars[i] == ' ':
					chars[i] = '%'
			image_list.append("".join(chars))
		except:
			pass
	return image_list


def main():

	index_directory = '/Users/karthikuppuluri/Desktop/index/'
	directory = '/Users/karthikuppuluri/Desktop/RawData/'
	search_engine = Engine(index_directory, fresh=True)
	time = search_engine.re_index(directory)
	print "time taken to index raw data: ", time

if __name__ == '__main__': 
	main()







