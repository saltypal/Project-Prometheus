from peer import Peer
import threading
import time


def main():
    print("Simple P2P peer (mesh) — you can listen for peers and connect to multiple peers.")
    peer = Peer(on_message=on_message)

    try:
        while True:
            print('\nMenu:')
            print('  1) Start listening on port')
            print('  2) Connect to a peer')
            print('  3) List connected peers')
            print('  4) Send message to all peers')
            print('  5) Quit')
            choice = input('Choose an option [1-5]: ').strip()

            if choice == '1':
                port = input('Enter port to listen on (default 12345): ').strip() or '12345'
                try:
                    port = int(port)
                    peer.start_listening(port=port)
                    print(f'[*] Listening on port {port}')
                except Exception as e:
                    print(f'[!] Could not start listening: {e}')

            elif choice == '2':
                host = input("Enter peer IP: ").strip()
                port = input('Enter peer port (default 12345): ').strip() or '12345'
                try:
                    port = int(port)
                    peer.connect(host, port)
                    print(f'[*] Connected to {host}:{port}')
                except Exception as e:
                    print(f'[!] Could not connect: {e}')

            elif choice == '3':
                peers = peer.list_peers()
                if not peers:
                    print('[*] No connected peers')
                else:
                    print('[*] Connected peers:')
                    for p in peers:
                        print('   -', p)

            elif choice == '4':
                msg = input('You: ')
                if msg:
                    peer.broadcast(msg)

            elif choice == '5':
                print('[*] Shutting down...')
                break

            else:
                print('Invalid choice')

    except KeyboardInterrupt:
        print('\n[Interrupted — shutting down]')

    finally:
        peer.shutdown()
        # give threads a moment to close
        time.sleep(0.2)


def on_message(conn, text):
    print(f"\n{conn.name}: {text}")
    print('You: ', end='', flush=True)


if __name__ == '__main__':
    main()
