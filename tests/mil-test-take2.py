import random
import time
import string
import os


count = 0
end_count = 1000000
directory = '/Users/karthikuppuluri/Desktop/mil-test/'

def update_directory(directory):

	# if toss == 0: breadth, elif 1: depth, else: stay with same directory
	toss = random.choice([0, 1, 2])
	if toss == 0:
		directory = os.path.split(directory)[0] + random.choice(string.lowercase) + '/'
	elif toss == 1: 
		directory = directory + random.choice(string.lowercase) + '/'
	else:
		pass

	return directory


while count <= end_count:

	add = [random.choice(string.uppercase) for i in range(20)]
	add = ''.join(add)
	add += '.txt'
	f = open(os.path.join(directory, add), 'w')
	f.close()

	print "added file to directory: ", [add, directory]

	count += 1
	if count % 10000 == 0:
		directory = update_directory(directory)
		if not os.path.isdir(directory):
			os.mkdir(directory)

