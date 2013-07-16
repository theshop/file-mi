from searchEngine import Engine 
from engine import open_dir
import argparse

"""
indexing a whole directory as an event based indexer would.
"""
"""
parser = argparse.ArgumentParser(description="the index directory")
parser.add_argument("index_directory", help="the index_directory to refresh")
parser.add_argument("query", help="the index_directory to refresh")
args = parser.parse_args()
index_directory = args.index_directory
query = args.query
search_engine = Engine(index_directory)
hits = search_engine.query(unicode(query))


print "query and hit: ", [query, hits[0], len(hits[0])]
"""


index_directory = '/Users/karthikuppuluri/Code/myproject/venv/myproject/index/'
ix = open_dir(index_directory)


with ix.searcher() as searcher:

	for fields in searcher.all_stored_fields():
		indexed_path = fields['path']
		print "indexed_path: ", indexed_path

		

search_engine = Engine(index_directory)
query = unicode('jpg')
hits1 = search_engine.query(query)
query2 = unicode('/srv/samba/share/SilaData/RawData/Arbin4/MITS_PRO/Settings/SysConfig_Channel_layout.stg')
hits2 = search_engine.query(query2)

print "result of syb: ", [hits1[0], len(hits1[0])]
print "result of exact file: ", [hits2[0], len(hits2[0])]