# goal: 20 bytes [clientID][]
# PAL000-<12 random bytes>

normal = bytes(b"-PAL000-".encode('utf-8'))
# normal = b'-SALPAL-'
print(normal)

import random
# x = bytes(str(random.randint(100000000000,999999999999)).encode('utf-8'))
# the above is worng becuase, im generating digits not bytes,
"""The bytes you're actually getting are the ASCII codes for the characters '1', '2', '3', etc. 
These are not truly random bytes. A truly random byte can be any value from 0 to 255 (\x00 to \xff).
 Your method only generates bytes from the small set of numbers that represent digits"""
x = bytes(random.randint(0,255) for _ in range(12))
s = normal+x
print(s)
print(len(s))