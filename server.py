from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import json, sys

class RequestHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", self.headers["Origin"])
        self.send_header("Access-Control-Allow-Credentials", "true")
        BaseHTTPRequestHandler.end_headers(self)
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/puzzles":
            self.randomPuzzleRetrieve()
    def do_POST(self):
        if self.path == "/puzzles":
            self.handlePuzzleAnalysis()
    def do_PUT(self):
        pass
    def do_DELETE(self):
        pass

    def handlePuzzleAnalysis(self):
        length = int(self.headers["Content-length"])
        puzzleImage = self.rfile.read(length)
        print("Begin: Printing puzzle...")
        print(puzzleImage)
        print("End: Puzzle printed.")
        boardLayout = {"puzzle_layout" : "2s0n7s0n0n0n1s0n4s0n3s9s1s0n2s0n0n0n0n0n6s4s0n8s7s0n0n0n6s0n0n0n0n3s0n2s5s0n7s0n9s0n0n1s0n0n0n2s1s0n0n9s0n4s0n0n9s0n0n0n4s0n6s0n5s0n3s0n6s0n0n0n0n3s0n2s0n0n0n7s0n"}
        jsonData = json.dumps(boardLayout)
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(jsonData, "utf-8"))

    def randomPuzzleRetrieve(self):
        boardLayout = {"puzzle_layout" : "2s0n7s0n0n0n1s0n4s0n3s9s1s0n2s0n0n0n0n0n6s4s0n8s7s0n0n0n6s0n0n0n0n3s0n2s5s0n7s0n9s0n0n1s0n0n0n2s1s0n0n9s0n4s0n0n9s0n0n0n4s0n6s0n5s0n3s0n6s0n0n0n0n3s0n2s0n0n0n7s0n"}
        jsonData = json.dumps(boardLayout)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(jsonData, "utf-8"))



# General Methods
    def getParsedBody(self):
        length = int(self.headers["Content-length"])
        body = self.rfile.read(length).decode("utf-8")
        parsed_body = parse_qs(body)
        return parsed_body

    def handle404(self):
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes("Not Found.", "utf-8"))

    def handle422(self):
        self.send_response(422)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes("Invalid data entry.", "utf-8"))

    def handle401(self):
        self.send_response(401)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes("This request requires user authetication.", "utf-8"))

    def handle403(self):
        self.send_response(403)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes("Not authorized.", "utf-8"))


def main():
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    listen = ("0.0.0.0", port)
    server = HTTPServer(listen, RequestHandler)

    print("Listening...")
    server.serve_forever()
main()
