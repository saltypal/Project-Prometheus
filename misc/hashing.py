import hashlib

"""
Working of hashing.
"""

data = b"I am going to h#sh you"
print(data)
print(type(data))
sha1Da = hashlib.sha1(data).digest()
print(len(sha1Da))


