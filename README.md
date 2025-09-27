# Project-Prometheus
"Prometheus stole fire from the gods and gave it to man. For this he was chained to a rock and tortured for eternity"

Building a Bittorrent client

### About BitTorrent
BitTorrent is a Peer-to-Peer Approach of sharing or distributing files. Unlike traditional Client-Server Architecture, which relies on the idea of centralisation, P2P has onli peers and follows the idea of De-Centralisation.

 Instead of everyone taking from one source, the downloaders (peers) share with each other. The more people who are downloading a file, the more sources there are to download from, and theoretically, the faster it becomes for everyone. This collective is known as a swarm.

 #### Componenets of BitTorrent:

 1. The Torrent File:
  A .torrent file, also known as a metainfo file, is a small file that contains metadata about the files to be shared. It does not contain the actual content. 
  Inside a torrent file, you will find:
  - URL: The address of the Tracker 