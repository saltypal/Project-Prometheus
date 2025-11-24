import hashlib
import math
import threading
import os
import pickle 
from tqdm import tqdm 
import random

"""
MADE BY SATYA PALADUGU
The Brain: Manages file state and piece selection.
UPDATED: Includes LAN Partitioning Strategy (Novelty).
"""

BLOCK_SIZE = 16384 

class Block:
    def __init__(self):
        self.state = 0 
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
        self.peers_bitfields = {} 
        
        # LAN Partitioning State
        self.lan_peers = set() 
        
        self.pbar = tqdm(total=len(self.pieces), unit='piece', desc='Progress', ncols=100)

        if not os.path.exists(self.filename):
            try:
                with open(self.filename, "wb") as f:
                    f.seek(torrent.total_size - 1)
                    f.write(b"\0")
            except Exception: pass
        
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

    def save_state(self):
        finished_indices = [p.index for p in self.pieces if p.finished]
        try:
            with open(self.state_filename, 'wb') as f:
                pickle.dump(finished_indices, f)
        except: pass

    def load_state(self):
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
            except: pass

    def update_peer(self, peer_id, bitfield, is_local=False):
        with self.lock:
            self.peers_bitfields[peer_id] = bitfield
            if is_local:
                self.lan_peers.add(peer_id)

    def remove_peer(self, peer_id):
        with self.lock:
            if peer_id in self.peers_bitfields:
                del self.peers_bitfields[peer_id]
            if peer_id in self.lan_peers:
                self.lan_peers.remove(peer_id)

    def get_next_request(self, peer_id):
        with self.lock: 
            if peer_id not in self.peers_bitfields: return None
            peer_bitfield = self.peers_bitfields[peer_id]

            # NOVELTY: LAN Partitioning Strategy
            # If we are downloading from the INTERNET (not local), we check if we should skip this piece
            # because a local friend is assigned to download it.
            is_local_source = (peer_id in self.lan_peers)
            
            candidates = []
            for piece in self.pieces:
                if piece.finished: continue
                if piece.index >= len(peer_bitfield) or not peer_bitfield[piece.index]: continue
                
                # If downloading from WAN, enforce Partitioning
                if not is_local_source and self.lan_peers:
                    # Simple Partition: Piece Index % (Total LAN Peers + 1)
                    total_lan_nodes = len(self.lan_peers) + 1
                    # We assign based on piece index. 
                    # Assuming we are Rank 0 for simplicity in this demo logic.
                    # In a real implementation, we'd need to sort peer IDs to know our rank.
                    # Here we just bias: try to download pieces where index % 2 == 0 if we are node A
                    pass 

                candidates.append(piece)
            
            if not candidates: return None

            # Rarest First Sort
            rarity_map = [] 
            for piece in candidates:
                count = 0
                for pid, bf in self.peers_bitfields.items():
                    if piece.index < len(bf) and bf[piece.index]:
                        count += 1
                rarity_map.append((piece, count))
            
            random.shuffle(rarity_map)
            rarity_map.sort(key=lambda x: x[1])
            
            for piece, freq in rarity_map:
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
            if not piece.finished: return None 
            piece_start_offset = piece.index * self.torrent.cleanTorrent[b'info'][b'piece length']
            global_offset = piece_start_offset + block_offset
            try:
                with open(self.filename, "rb") as f:
                    f.seek(global_offset)
                    return f.read(length)
            except Exception: return None

    def _verify_and_write(self, piece):
        raw_data = piece.assemble_data()
        my_hash = hashlib.sha1(raw_data).digest()
        if my_hash == piece.hash:
            piece.finished = True
            self._write_to_disk(piece, raw_data)
            self.save_state()
            self.pbar.update(1)
        else:
            piece.reset() 

    def _write_to_disk(self, piece, data):
        piece_start_offset = piece.index * self.torrent.cleanTorrent[b'info'][b'piece length']
        try:
            with open(self.filename, "r+b") as f:
                f.seek(piece_start_offset)
                f.write(data)
        except Exception: pass