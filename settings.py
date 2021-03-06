"""
The Settings for the FileIndexer.
Once modified, run some restart command to get the entire FileIndexer back up and running with new settings.
"""


# Where the index directory is located:
INDEX_DIR = '/home/labuser/Code/FileIndexer/index_directory'

# Directory to monitor for changes to index
MONITORED_DIR = '/share/SilaData/'

# Directory to which generated thumbnails will be added to:
#THUMBNAIL_DIR = 

# Location of the log file for monitor:
MONITOR_LOG = '/home/labuser/Code/FileIndexer/monitor_log.txt'
MONITOR_LOG_RATE = 10

INDEXER_LOG = '/home/labuser/Code/FileIndexer/indexer_log.txt'
INDEXER_LOG_RATE = 10

# Directory of the thumbnail location, should match the thumbnail dir pointed to by the site
THUMBNAIL_DIR = '/Users/karthikuppuluri/Desktop/thumb/'

THUMB_EXTENSION = '.jpg'

THUMB_WIDTH = 500
THUMB_HEIGHT = 500