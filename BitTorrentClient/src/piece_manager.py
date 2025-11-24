import hashlib
import math
import threading
import os
import pickle # <--- For saving state
from tqdm import tqdm 

"""
MADE BY SATYA PALADUGU
The Brain: Manages file state, verifies pieces, and delegates blocks.
Updated for Phase 2: RESUME STATE (Persistence).
"""

BLOCK_SIZE = 16384 

class Block:
    def __init__(self):
        self.state = 0 # 0=Missing, 1=Pending, 2=Retrieved
        self.data = b''

class Piece:
    def __init__(self, index, length, hash_value):
        self.index = index
        self.length = length
        self.hash = hash_value
        self.finished = False 
        num_blocks = math.ceil(self.length / BLOCK_SIZE)
        self.blocks = [Block() for _ in range(num_blocks)]
        
    def reset(self):
        for block in self.blocks:
            block.state = 0
            block.data = b''
        self.finished = False

    def set_finished(self):
        """Mark piece as done (used when loading state)"""
        self.finished = True
        for block in self.blocks:
            block.state = 2 

    def is_complete(self):
        return all(b.state == 2 for b in self.blocks)

    def assemble_data(self):
        return b''.join([b.data for b in self.blocks])

class PieceManager:
    def __init__(self, torrent):
        self.torrent = torrent
        self.pieces = []
        self._init_pieces()
        
        self.lock = threading.Lock() 
        self.filename = f"downloaded_{torrent.info_hash.hex()[:6]}.dat"
        self.state_filename = self.filename + ".state"
        
        print(f"Storage: {self.filename}")
        
        # Initialize Progress Bar
        self.pbar = tqdm(total=len(self.pieces), unit='piece', desc='Progress', ncols=100)

        # Initialize File
        if not os.path.exists(self.filename):
            try:
                with open(self.filename, "wb") as f:
                    f.seek(torrent.total_size - 1)
                    f.write(b"\0")
            except Exception as e:
                print(f"Error creating file: {e}")
        
        # RESUME STATE
        self.load_state()
            
    def _init_pieces(self):
        piece_length = self.torrent.cleanTorrent[b'info'][b'piece length']
        total_length = self.torrent.total_size
        pieces_hashes = self.torrent.cleanTorrent[b'info'][b'pieces']
        num_pieces = math.ceil(total_length / piece_length)
        
        for i in range(num_pieces):
            if i == num_pieces - 1:
                this_length = total_length % piece_length
                if this_length == 0: this_length = piece_length 
            else:
                this_length = piece_length
            
            start = i * 20
            end = start + 20
            this_hash = pieces_hashes[start:end]
            self.pieces.append(Piece(i, this_length, this_hash))

    # --- STATE PERSISTENCE (PHASE 2) ---
    def save_state(self):
        """Save the list of finished piece indices"""
        finished_indices = [p.index for p in self.pieces if p.finished]
        try:
            with open(self.state_filename, 'wb') as f:
                pickle.dump(finished_indices, f)
            # print("State saved.")
        except Exception as e:
            print(f"Failed to save state: {e}")

    def load_state(self):
        """Load state and update progress"""
        if os.path.exists(self.state_filename):
            try:
                with open(self.state_filename, 'rb') as f:
                    finished_indices = pickle.load(f)
                
                count = 0
                for index in finished_indices:
                    if index < len(self.pieces):
                        self.pieces[index].set_finished()
                        count += 1
                
                self.pbar.update(count)
                print(f"Resumed: {count} pieces already downloaded.")
            except Exception as e:
                print(f"Failed to load state: {e}")

    # --- WORKER INTERFACE ---

    def get_next_request(self, peer_bitfield):
        with self.lock: 
            for piece in self.pieces:
                if piece.finished:
                    continue
                
                if piece.index < len(peer_bitfield) and peer_bitfield[piece.index]:
                    for block_index, block in enumerate(piece.blocks):
                        if block.state == 0: 
                            block.state = 1 
                            return piece.index, block_index * BLOCK_SIZE, min(BLOCK_SIZE, piece.length - (block_index * BLOCK_SIZE))
            return None

    def block_received(self, piece_index, begin, data):
        with self.lock: 
            piece = self.pieces[piece_index]
            block_index = begin // BLOCK_SIZE
            
            block = piece.blocks[block_index]
            block.data = data
            block.state = 2 
            
            if piece.is_complete():
                self._verify_and_write(piece)

    def read_block(self, piece_index, block_offset, length):
        with self.lock:
            piece = self.pieces[piece_index]
            if not piece.finished:
                return None 
            
            piece_start_offset = piece.index * self.torrent.cleanTorrent[b'info'][b'piece length']
            global_offset = piece_start_offset + block_offset
            
            try:
                with open(self.filename, "rb") as f:
                    f.seek(global_offset)
                    data = f.read(length)
                    return data
            except Exception:
                return None

    def _verify_and_write(self, piece):
        raw_data = piece.assemble_data()
        my_hash = hashlib.sha1(raw_data).digest()
        
        if my_hash == piece.hash:
            piece.finished = True
            self._write_to_disk(piece, raw_data)
            self.save_state() # <--- AUTO SAVE on success
            self.pbar.update(1)
        else:
            piece.reset() 

    def _write_to_disk(self, piece, data):
        piece_start_offset = piece.index * self.torrent.cleanTorrent[b'info'][b'piece length']
        try:
            with open(self.filename, "r+b") as f:
                f.seek(piece_start_offset)
                f.write(data)
        except Exception as e:
            print(f"DISK I/O ERROR: {e}")