from collections import deque

"""

MADE BY SATYA PALADUGU AT 27/9/2025 9:40 AM

This python file deals with bencoding. Bencoding is a way to specify and organize data in a terse format. 
It supports the following types: byte strings, integers, lists, and dictionaries.

This file takes the torrent file as input, parses it and retrieves information.

Bencoding format:
Byte strings are encoded as follows: <string length encoded in base ten ASCII>:<string data>
Integers are encoded as follows: i<integer encoded in base ten ASCII>e
Lists are encoded as follows: l<bencoded values>e
Dictionaries are encoded as follows: d<bencoded string><bencoded element>e
"""

class benDecoder:
    """

This class contains the methods to decode a bencoded string.
    
We will push the whole thing into a queue.

As we keep going, we keep popping from left of the queue.

And every element we pop from the queue will be put into a function.
    
    """

    def __init__(self, fileName):
        self.fileName = fileName
        self.read_file()

    def crc(data):
        return chr(data)

    def read_file(self):
        print("Reading the file.... ")
        try:
            with open(self.fileName, 'rb') as tFile:
                torrentContent = tFile.read()
                print("Done queueing the torrent file contents.")

                return deque(torrentContent)

        except Exception as e:
            print(f"Error Reading: {e}")


    def bendiString(data, len):
        """
         4: spam represents the string "spam"

        """
        data.popleft # we are poopping ':'
        n = 0
        str = b''
        while len != n:
            str += bytes([data.popleft()])
            n+=1
        return str
        
    def bendiList(self,data):
        """
        Example: l4:spam4:eggse represents the list of two strings: [ "spam", "eggs" ]
        Example: le represents an empty list: []        

        """
        blist = []
        while data[0]!=ord('e'):
            len = data.popleft()
            blist.append(self.bendiString(data,len))
        return blist
    
    def bendiIntegers(data):
        """ 
        Example: i3e represents the integer "3"
        Example: i-3e represents the integer "-3"
        """
        str = b''
        while data[0]!=ord('e'):
            str += bytes([data.popleft()])
        
        data.popleft() # to remove e
        return int(str)
        
    def bendiDictionaries(self,data):
        """
        Example: d3:cow3:moo4:spam4:eggse represents the dictionary { "cow" => "moo", "spam" => "eggs" }
        Example: d4:spaml1:a1:bee represents the dictionary { "spam" => [ "a", "b" ] }
        Example: d9:publisher3:bob17:publisher-webpage15:www.example.com18:publisher.location4:homee represents { "publisher" => "bob", "publisher-webpage" => "www.example.com", "publisher.location" => "home" }
        Example: de represents an empty dictionary {}
        """
        dict = {}
        while data[0]!=ord('e'):
            # first word
            len1 = data.popleft()
            word1=self.bendiString(data,len1)
            len2 = data.popleft()
            word2 = self.bendiString(data,len2)
            dict[word1] = word2
            
        return dict
    

    def deBencode_list(self):
        data = self.read_file()
        data.append('~')

        global_list = [] # here is where we add everything.

        while data:
            #So, while my data queue is there, i will pop my first element.

            character = chr(data.popleft()) # because everything is in binary, i will need to make it into character.

            if character.isdigit(): # If the character is digit, then the upcoming is a String
                len = character # the length of the String.
                global_list.append(self.bendiString(data, len)) #making next 'len' elements into string and appending to  global_list
            
            
            elif character == 'i': # this means it is a string
                    global_list.append(self.bendiIntegers(data)) # appending the integers into the global_list
            
            elif character == 'l': # this means it is a list
                    global_list.append(self.bendiList(data))
            elif character == 'd':
                    global_list.append(self.bendiDictionaries(data)) # dictioaries can be appended too.
            elif character =='~':
                    return global_list.reverse()
        if len(global_list) != 1:
            raise ValueError("Bencode decoding failed. Final stack state is not a single item.")

if __name__ == '__main__':
    test = 'test.torrent'
    obj = benDecoder(test)
    decoded = obj.deBencode_list()
    print(decoded)