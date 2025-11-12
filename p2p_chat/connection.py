import socket
import threading
import traceback


class Connection:

    def __init__(self, sock: socket.socket, addr=None, on_message=None, name=None):
        self.sock = sock
        self.addr = addr
        self.on_message = on_message
        if name:
            self.name = name
        elif addr and len(addr) >= 2:
            self.name = f"{addr[0]}:{addr[1]}"
        else:
            self.name = 'peer'
        self._stop = threading.Event()
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
                    text = '[non-text data]'

                if self.on_message:
                    try:
                        self.on_message(self, text)
                    except Exception:
                        traceback.print_exc()
        finally:
            self.close()

    def send(self, text: str):
        try:
            self.sock.send(text.encode('utf-8'))
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
