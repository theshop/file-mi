import os
import sys
import random
import string

DIR = '/Users/karthikuppuluri/Desktop/TEXT'

for i in range(30000):

	add = [random.choice(string.letters) for i in range(10)]
	add = ''.join(add)
	add += '.txt'
	f = open(os.path.join(DIR, add), 'w')
	f.write('a')
	f.close()


