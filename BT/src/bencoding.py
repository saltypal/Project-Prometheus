import pprint
from collections import deque

"""
MADE BY SATYA PALADUGU AT 27/9/2025 9:40 AM
LAST MODIFIED: 29/9/2025 11:57AM 
SUPER ULTRA IMPORTANT NOTEEEEEEE:
         We will not maintain any while loop or make it a recursive call within this bencodeDecode() function.
         in general, the torrentfile doesnt have integers or strings sitting alone and all
         what happens is, the torrent file is always made up of dictionaries and lists. 
         which means, recursion should happen within the main fucntions of the dictionary and list functions only.
         benDecide fucntion is just the classifier and claling of the function needed for that decoding
         I HOPE IT IS CLEAR. 
         MORE CAN BE READ HERE: https://wiki.theory.org/BitTorrentSpecification#Scope
        
SECOND IMPORTANT NOTE:
         if you see any ai code or any other implementation of bencodeDECODER, you will see a different logic.
         this uses queue logic so yeah. dont assume this is ultra fast either, it isnt. you also know that. but yeah as long as it works, it works.
         BUT THE BENCODER IS AI GENERATED.
THIRDLY: 
         yes according to the norm, I have to write an encoder too. BUT SADLY, IM TOO LAZY.
         so for the part where i have to get hash of the info dict, i am going to do a different way. 
         check tracker.py

         

This python file deals with bencoding. Bencoding is a way to specify and organize data in a terse format. 
It supports the following types: byte strings, integers, lists, and dictionaries.

This file takes the torrent file as input, parses it and retrieves information.

Bencoding format:
Byte strings are encoded as follows: <string length encoded in base ten ASCII>:<string data>
Integers are encoded as follows: i<integer encoded in base ten ASCII>e
Lists are encoded as follows: l<bencoded values>e
Dictionaries are encoded as follows: d<bencoded string><bencoded element>e
"""

class bencodeDecode:
    """

        This class contains the methods to Decode a bencoded string.

        The input for this function is queue.
            
        We will push the whole thing into a queue.

        As we keep going, we keep popping from left of the queue.

        And every element we pop from the queue will be put into a function.
    
    """
    
    def bendiString(self, data):
        # print("string")
        """
        4:spam represents the string "spam"
        """
        # Read length until ':'                                    why until :?? because the string can be more than one digit also
        length_bytes = b''
        while data and chr(data[0]) != ':':
            length_bytes += bytes([data.popleft()])
        
        data.popleft()  # Remove ':'
        length = int(length_bytes)
        
        # Read the string data
        result = b''
        for _ in range(length):
            result += bytes([data.popleft()])  # Pop and append that
        return result
        
    def bendiList(self,data):
        # print("list")
        """
        Example: l4:spam4:eggse represents the list of two strings: [ "spam", "eggs" ]
        Example: le represents an empty list: []        

        """
        data.popleft()  # Remove 'l'
        blist = []
        while data and chr(data[0]) != 'e':
            blist.append(self.bencodeDecode(data))  
        data.popleft()  # Remove 'e'
        return blist
    
    def bendiIntegers(self,data):
        # print("integer")
        """ 
        Example: i3e represents the integer "3"
        Example: i-3e represents the integer "-3"
        """
        data.popleft()  # Remove 'i'
        num_str = b''
        while data and chr(data[0]) != 'e':
            num_str += bytes([data.popleft()]) # Pop and append.
        data.popleft()  # Remove 'e'
        return int(num_str.decode('ascii')) 
        
    def bendiDictionaries(self,data):
        # print("dictionary")
        """
        Example: d3:cow3:moo4:spam4:eggse represents the dictionary { "cow" => "moo", "spam" => "eggs" }
        Example: d4:spaml1:a1:bee represents the dictionary { "spam" => [ "a", "b" ] }
        Example: d9:publisher3:bob17:publisher-webpage15:www.example.com18:publisher.location4:homee represents { "publisher" => "bob", "publisher-webpage" => "www.example.com", "publisher.location" => "home" }
        Example: de represents an empty dictionary {}
        """
        data.popleft()  # Remove 'd'
        result = {}
        while data and chr(data[0]) != 'e':
            key = self.bencodeDecode(data)    # word one
            value = self.bencodeDecode(data)  # word two
            result[key] = value
        data.popleft()  # Remove 'e'
        return result
    
    def bencodeDecode(self, data):
        """
        Main recursive bencodeDecode method

        """
        if not data:
            raise ValueError("\nwhat ra this? Data didnt end properly. Missing ")
        
        char = chr(data[0]) # I wont pop the first character from the queue. But i will just check it.
        if char.isdigit():
            return self.bendiString(data)
        elif char == 'i':
            return self.bendiIntegers(data)
        elif char == 'l':
            return self.bendiList(data)
        elif char == 'd':
            return self.bendiDictionaries(data)
        else:
            raise ValueError(f"\nWrong bencoding start not valid format. what man this?what u did here? :{char}")

    def deBencode_list(self,data):
        self.data = data
        """
        bencodeDecode the entire torrent file
        """
        result = self.bencodeDecode(self.data)
        if self.data:  # Should be empty after successful bencodeDecode
            raise ValueError("\nExtra data after decoding")
        return result


# class bencodeEncode:

