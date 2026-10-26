# provisório até o agendador ficar pronto
import socket
import time

print(f"agendador provisório em {socket.gethostname()}")
while True:
    time.sleep(60)
