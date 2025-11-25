import os
import hashlib
import json
import socket
import threading
import time

CHUNK_SIZE = 256 * 1024  # 256KB chunks

class BitTorrentManager:
    def __init__(self, port=6882):
        self.port = port
        self.seeding_files = {}  # file_hash -> file_path
        self.running = True
        self.server_thread = threading.Thread(target=self._start_server, daemon=True)
        self.server_thread.start()

    def _start_server(self):
        """Start a simple TCP server to serve chunks"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Try to bind to the port, if taken, try next few
            for i in range(10):
                try:
                    self.sock.bind(('0.0.0.0', self.port + i))
                    self.port += i
                    break
                except OSError:
                    continue
            
            self.sock.listen(5)
            print(f"[BitTorrent] Seeder listening on port {self.port}")
            
            while self.running:
                try:
                    client, addr = self.sock.accept()
                    threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()
                except Exception as e:
                    print(f"[BitTorrent] Accept error: {e}")
        except Exception as e:
            print(f"[BitTorrent] Server error: {e}")

    def _handle_client(self, client):
        """Handle incoming chunk requests"""
        try:
            # Protocol: JSON request
            # Payload: {"file_hash": "...", "chunk_index": 0}
            
            data = client.recv(1024).decode('utf-8').strip()
            if not data:
                return
                
            try:
                request = json.loads(data)
            except json.JSONDecodeError:
                return

            file_hash = request.get('file_hash')
            chunk_index = request.get('chunk_index')
            
            if file_hash in self.seeding_files:
                file_path = self.seeding_files[file_hash]
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        f.seek(chunk_index * CHUNK_SIZE)
                        chunk_data = f.read(CHUNK_SIZE)
                        client.sendall(chunk_data)
                else:
                    print(f"[BitTorrent] File not found on disk: {file_path}")
            else:
                print(f"[BitTorrent] Requested file hash not found: {file_hash}")
                
        except Exception as e:
            print(f"[BitTorrent] Client handler error: {e}")
        finally:
            client.close()

    def create_torrent(self, file_path):
        """Create a torrent descriptor for a file"""
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        chunks = []
        
        hasher = hashlib.sha1()
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                # Store hash of each chunk
                chunks.append(hashlib.sha1(chunk).hexdigest())
                hasher.update(chunk)
                
        file_hash = hasher.hexdigest()
        self.seeding_files[file_hash] = file_path
        
        return {
            'filename': filename,
            'size': file_size,
            'file_hash': file_hash,
            'chunks': chunks,
            'chunk_size': CHUNK_SIZE,
            'seeder_port': self.port
        }

    def download_file(self, torrent_data, save_path, peer_ip, peer_port, progress_callback=None):
        """Download file from a peer"""
        file_hash = torrent_data['file_hash']
        chunks = torrent_data['chunks']
        total_chunks = len(chunks)
        
        try:
            with open(save_path, 'wb') as f:
                # Pre-allocate file (optional, but good practice)
                # f.truncate(torrent_data['size'])
                
                for i, chunk_hash in enumerate(chunks):
                    success = False
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.settimeout(10)
                        s.connect((peer_ip, int(peer_port)))
                        
                        req = json.dumps({
                            'file_hash': file_hash,
                            'chunk_index': i
                        })
                        s.send(req.encode('utf-8'))
                        
                        # Read chunk data
                        chunk_data = b""
                        expected_size = CHUNK_SIZE
                        # Last chunk might be smaller
                        if i == total_chunks - 1:
                            expected_size = torrent_data['size'] % CHUNK_SIZE or CHUNK_SIZE

                        while len(chunk_data) < expected_size:
                            packet = s.recv(4096)
                            if not packet:
                                break
                            chunk_data += packet
                        
                        # Verify hash
                        if hashlib.sha1(chunk_data).hexdigest() == chunk_hash:
                            f.write(chunk_data)
                            success = True
                        else:
                            print(f"[BitTorrent] Chunk {i} hash mismatch")
                            
                        s.close()
                    except Exception as e:
                        print(f"[BitTorrent] Failed to download chunk {i} from {peer_ip}: {e}")
                    
                    if not success:
                        print(f"[BitTorrent] Failed to download chunk {i}")
                        return False
                    
                    if progress_callback:
                        progress_callback(int((i + 1) / total_chunks * 100))
                        
            return True
        except Exception as e:
            print(f"[BitTorrent] Download error: {e}")
            return False
