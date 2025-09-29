import pprint
from collections import deque


"""
MADE BY SATYA PALADUGU AT 27/9/2025 9:40 AM
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
Dicti