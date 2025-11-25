import socket
import threading
import traceback
import json


class Connection:

    def __init__(self, sock: socket.socket, addr=None, on_message=None, name=None):
        self.sock = sock
        self.addr = addr
        self.on_message = on_message
        self.username = None  # will be set after handshake
        if name:
            self.name = name
        elif addr and len(addr) >= 2:
            self.name = f"{addr[0]}:{addr[1]}"
        else:
            self.name = 'peer'
        self._stop = threading.Event()
        self._buffer = ""  # buffer for line-delimited messages
        self._thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._thread.start()

    def _recv_loop(self):
        try:
            while not self._stop.is_set():
                try:
                    data = self.sock.recv(1024)
                except ConnectionResetError:
                    break
                except OSError:
                    break

                if not data:
                    break

                try:
                    text = data.decode('utf-8')
                except UnicodeDecodeError:
                    continue  # skip invalid data

                self._buffer += text
                
                # Process complete lines (newline-delimited messages)
                while '\n' in self._buffer:
                    line, self._buffer = self._buffer.split('\n', 1)
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        message_obj = json.loads(line)
                        if self.on_message:
                            try:
                                self.on_message(self, message_obj)
                            except Exception:
                                traceback.print_exc()
                    except json.JSONDecodeError:
                        # Handle legacy plain text for compatibility
                        if self.on_message:
                            try:
                                self.on_message(self, {"type": "text", "text": line})
                            except Exception:
                                traceback.print_exc()
        finally:
            self.close()

    def send(self, text: str):
        """Legacy send method for plain text (deprecated, use send_json)"""
        try:
            self.sock.send(text.encode('utf-8'))
        except Exception:
            raise
    
    def send_json(self, obj: dict):
        """Send a JSON object as a newline-delimited message"""
        try:
            message = json.dumps(obj) + '\n'
            self.sock.send(message.encode('utf-8'))
        except Exception:
            raise

    def close(self):
        # idempotent close
        if self._stop.is_set():
            return
        self._stop.set()
        try:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            self.sock.close()
        except Exception:
            pass

    def is_alive(self):
        return self._thread.is_alive()
