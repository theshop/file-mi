import Image
import os
import sys
import time
import shutil

"""
This file contains the Thumber class that provides all the thumbnailing functions.
"""

class Thumber:

	def __init__(self, width, height, thumbnail_dir, extension):

		self.width = width
		self.height = height
		self.thumbnail_dir = thumbnail_dir
		self.extension = extension

	"""
	This method takes image url and replaces '/' with '-' and ends with thumb to store in thumbnail directory
	input: image_location
	output: time_taken to to thumbnail
	"""
	def thumb(self, image_location, destination):

		t0 = time.time()
		im = Image.open(image_location)
		size = self.width, self.height
		im.thumbnail(size, Image.ANTIALIAS)
		outfile = self.convert_url(image_location, destination, True)
		
		if os.path.exists(outfile):
			os.remove(outfile)

		im.save(outfile, "JPEG")
		t1 = time.time()
		return t1 - t0


	"""
	If forward=True: converts input url into the format to save the thumbnail.
	else converts the formatted url back to original
	input: image_url, forward
	output: formatted/de-formatted url
	"""
	def convert_url(self, image_url, destination, forward):

		if forward: 
			file_name, ext = os.path.splitext(image_url)
			file_name = file_name.replace('/', '-')
			file_name = file_name[1:]
			ext = ext.replace('.', '-')
			out = destination + file_name + ext + self.extension
			return out

		else:
			arr = list(image_url)
			for i in range(len(destination)):
				arr.pop(0)
			for i in range(len(self.extension)):
				arr.pop()
			index = ''.join(arr).rfind('-')
			arr[index] = '.'
			out = ''.join(arr)
			out = out.replace('-', '/')
			out = '/' + out
			return out


	def thumb_dir(self, directory_path):

		t0 = time.time()
		self.__thumb_path(directory_path)
		t1 = time.time()
		return t1 - t0

	# recursive function that indexes an object if it is a file, else it traverses into that directory and continues

	def __thumb_path(self, path):

		if os.path.isfile(path):
			try:
				Image.open(path)
				out = self.thumb(path, self.thumbnail_dir)
			except:
				pass
		elif os.path.isdir(path):
			# This means that the path is to a directory, not a file
			ls = os.listdir(path)
			for i in ls:
				self.__thumb_path(os.path.join(path, i))
		else:
			pass


def main():

	t = Thumber(500, 500)
	time_taken = t.thumb_dir('/Users/karthikuppuluri/Desktop/BET')
	#time_taken = t.thumb('/Users/karthikuppuluri/Desktop/AN.jpg', t.thumbnail_dir)
	print "time taken:", time_taken

if __name__ == '__main__':
	main()
