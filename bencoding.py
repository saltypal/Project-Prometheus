import pprint
from collections import deque

"""

MADE BY SATYA PALADUGU AT 27/9/2025 9:40 AM
SUPER ULTRA IMPORTANT NOTEEEEEEE:
         We will not maintain any while loop or make it a recursive call within this benDecode() function.
         in general, the torrentfile doesnt have integers or strings sitting alone and all
         what happens is, the torrent file is always made up of dictionaries and lists. 
         which means, recursion should happen within the main fucntions of the dictionary and list functions only.
         benDecide fucntion is just the classifier and claling of the function needed for that decoding
         I HOPE IT IS CLEAR. 
         MORE CAN BE READ HERE: https://wiki.theory.org/BitTorrentSpecification#Scope
        
SECOND IMPORTANT NOTE:
         if you see any ai code or any other implementation of bencoder, you will see a different logic.
         this uses queue logic so yeah. dont assume this is ultra fast either, it isnt. you also know that. but yeah as long as it works, it works.
THIRDLY: 
         File >>> (Read in binary mode rb) >>> Single bytes object.

         Bencoded bytes object >>> (Bencoding parser) >>> Python dictionary with bytes and int values.

         Specific bytes values >>> (.decode('utf-8')) >>> Human-readable str values.

         so yeah this whole decode utf-8 code is ai :thumbsup:

         

This python file deals with bencoding. Bencoding is a way to specify and organize data in a terse format. 
It supports the following types: byte strings, integers, lists, and dictionaries.

This file takes the torrent file as input, parses it and retrieves information.

Bencoding format:
Byte strings are encoded as follows: <string length encoded in base ten ASCII>:<string data>
Integers are encoded as follows: i<integer encoded in base ten ASCII>e
Lists are encoded as follows: l<bencoded values>e
Dictionaries are encoded as follows: d<bencoded string><bencoded element>e
"""

class benDecode:
    """

This class contains the methods to benDecode a bencoded string.
    
We will push the whole thing into a queue.

As we keep going, we keep popping from left of the queue.

And every element we pop from the queue will be put into a function.
    
    """

    def __init__(self, fileName):
        self.fileName = fileName
        self.data = self.read_file()


    def read_file(self):
        print("Reading the file.... ")
        try:
            with open(self.fileName, 'rb') as tFile:
                torrentContent = tFile.read()
                print("Done queueing the torrent file contents.")

                return deque(torrentContent)

        except Exception as e:
            print(f"Error Reading: {e}")


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
            blist.append(self.benDecode(data))  
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
            key = self.benDecode(data)    # word one
            value = self.benDecode(data)  # word two
            result[key] = value
        data.popleft()  # Remove 'e'
        return result
    
    def benDecode(self, data):
        """
        Main recursive benDecode method

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
            raise ValueError(f"\nWrong bencoding start not valid format. what ra you. what u did here? :{char}")

    def deBencode_list(self):
        """
        benDecode the entire torrent file
        """
        result = self.benDecode(self.data)
        if self.data:  # Should be empty after successful benDecode
            raise ValueError("\nExtra data after decoding")
        return result

    def _clean_output(self, data):
        """
        Recursively traverses the data structure and decodes byte strings to
        UTF-8 strings where possible. Leaves binary data as bytes.
        """
        if isinstance(data, bytes):
            try:
                return data.decode('utf-8')
            except UnicodeDecodeError:
                return data  # This is binary data, leave it as bytes
        elif isinstance(data, list):
            return [self._clean_output(item) for item in data]
        elif isinstance(data, dict):
            return {
                self._clean_output(key): self._clean_output(value)
                for key, value in data.items()
            }
        else:
            return data # It's an int, return as is

    def write_to_file(self, result):
        if result:
            print("\nDecoding is done. Congratulations ma.")
            cleaned_result = self._clean_output(result)
            with open('torrentData','w', encoding='utf-8') as writer:
                writer.write(pprint.pformat(cleaned_result))
        else: print("\nsorry boss nothing to print only. empty shit.")
   
if __name__ == '__main__':
    # IMPORTANT: Change this path to your test torrent file
    torrent_file_path = 'test.torrent' 
    
    # This block now handles errors gracefully.
    try:
        benDecoder = benDecode(torrent_file_path)
        benDecoded_data = benDecoder.deBencode_list()
        benDecoder.write_to_file(benDecoded_data)
    except Exception as e:
        print(f"\nerrorrrrrrrr {e}")


# ppprint
# It improves the readability of data, especially 
# for nested lists, dictionaries, and other complex 
# objects, by adding indentation and line breaks to
# make the structure clear. This is particularly useful 
# when dealing with API responses, large JSON files, 
# or intricate data structures during debugging.

 # def deBencode_list(self):
    #     data = self.read_file()
    #     data.append('~')

    #     global_list = [] # here is where we add everything.

    #     while data:
    #         #So, while my data queue is there, i will pop my first element.

    #         character = chr(data.popleft()) # because everything is in binary, i will need to make it into character.

    #         if character.isdigit(): # If the character is digit, then the upcoming is a String
    #             len = character # the length of the String.
    #             global_list.append(self.bendiString(data, len)) #making next 'len' elements into string and appending to  global_list
            
            
    #         elif character == 'i': # this means it is a string
    #                 global_list.append(self.bendiIntegers(data)) # appending the integers into the global_list
            
    #         elif character == 'l': # this means it is a list
    #                 global_list.append(self.bendiList(data))
    #         elif character == 'd':
    #                 global_list.append(self.bendiDictionaries(data)) # dictioaries can be appended too.
    #         elif character =='~':
    #                 return global_list.reverse()
    #     if len(global_list) != 1:
    #         raise ValueError("Bencode decoding failed. Final stack state is not a single item.")
