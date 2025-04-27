from BotServer.MainServer import MainServer
import signal
import time
import sys

Bot_Logo = """

 _______  .______   .______     ______   .___________.
|       \ |   _  \  |   _  \   /  __  \  |           |
|  .--.  ||  |_)  | |  |_)  | |  |  |  | `---|  |----`
|  |  |  ||   ___/  |   _  <  |  |  |  |     |  |     
|  '--'  ||  |      |  |_)  | |  `--'  |     |  |     
|_______/ | _|      |______/   \______/      |__|     
                                                      
     Version: V1.0
     Author: 大鹏                                             

"""


def shutdown(signum, frame):
    Ms.Pms.stopPushServer()
    time.sleep(2)
    sys.exit(0)


if __name__ == '__main__':
    Ms = MainServer()
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    try:
        Ms.processMsg()
    except KeyboardInterrupt:
        shutdown(signal.SIGINT, None)
