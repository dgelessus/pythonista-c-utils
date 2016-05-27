import os
import shutil
import sys

DEST = os.path.join(os.path.dirname(__file__), "cffipp", "include_private", "frameworks")

def copy_framework_headers(src, dest=DEST):
	os.makedirs(dest, exist_ok=True)
	
	for file in os.listdir(src):
		name, ext = os.path.splitext(file)
		if ext != ".framework":
			continue
		
		if not os.path.exists(os.path.join(src, file, "Headers")):
			print("{} has no Headers folder, skipping.".format(file))
			continue
		
		print(file)
		shutil.copytree(os.path.join(src, file, "Headers"), os.path.join(dest, name))

if __name__ == "__main__":
	copy_framework_headers(sys.argv[1])

