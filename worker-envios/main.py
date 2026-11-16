# provisório até o worker-envios ficar pronto
import socket
import time

print(f"worker-envios provisório em {socket.gethostname()}")
while True:
    time.sleep(60)
