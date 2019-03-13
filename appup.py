import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    datefmt="[%Y-%m-%d][%H:%M:%S]:",
                    level=logging.INFO)
logger = logging.getLogger(__name__)


"""
this simple webserver is intended to provide a nonblocking endpoint to control application availability.
"""

class UptimeHandler(BaseHTTPRequestHandler):

    #Handler for the GET requests
    def do_GET(self):
        upfile = os.getenv('UP_FILE', '/pod/up.txt')
        if self.path == '/up':
            try:
                if not os.path.exists(upfile):
                    logger.info("creating upfile")
                    os.mknod(upfile)
                else:
                    logger.info("app is already up")
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes("app is up", "utf-8"))
            except Exception as e:
                logger.error(e)
                self.send_response(503)
        elif self.path == '/down':
            try:
                if os.path.exists(upfile):
                    logger.info("removing upfile")
                    os.remove(upfile)
                else:
                    logger.info("app is already down")
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes("app is down", "utf-8"))
            except Exception as e:
                logger.error(e)
                self.send_response(503)
        elif self.path == '/health':
            try:
                if os.path.exists(upfile):
                    logger.info("app is up")
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(bytes("app is up", "utf-8"))
                else:
                    logger.info("app is down")
                    self.send_response(503)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(bytes("app is down", "utf-8"))
            except Exception as e:
                logger.error(e)
                self.send_response(503)
        else:
            self.send_response(404)

def main(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    ## set variables
    upfile      = os.getenv('UP_FILE', '/pod/up.txt')
    server_port = os.getenv('UP_PORT', 9999)

    server = HTTPServer(('', int(server_port)), UptimeHandler)
    logger.info("starting appup service on {0}".format(server_port))

    #Wait forever for incoming http requests
    server.serve_forever()

if __name__== "__main__":
  main()
