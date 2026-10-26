# provisório até o worker-boletos ficar pronto
import socket
import time

print(f"worker-boletos provisório em {socket.gethostname()}")
while True:
    time.sleep(60)
