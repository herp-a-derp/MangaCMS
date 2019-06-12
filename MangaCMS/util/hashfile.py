
import hashlib

def hash_file(filepath):

	with open(filepath, "rb") as f:
		hash_md5 = hashlib.md5()
		hash_md5.update(f.read())
		fhash = hash_md5.hexdigest()
	return fhash

def hash_bytes(filebytes):
	hash_md5 = hashlib.md5()
	hash_md5.update(filebytes)
	fhash = hash_md5.hexdigest()
	return fhash