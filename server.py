from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import sys
from puzzleprocessor import PuzzleProcessor
from digitpredictor import DigitPredictor

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
        digitPredictor = DigitPredictor()
        length = int(self.headers["Content-length"])
        puzzleImage = self.rfile.read(length)
        print("Processing puzzle image...")
        #try:
        puzzleProcessor = PuzzleProcessor(puzzleImage)
        cellsWithDigits = puzzleProcessor.extractDigitContainingCells()
        #except Exception as e:
        #    print(e)
        print("Labeling cells with digits...")
        layout = "000604700706000009000005080070020093800000005430010070050200000300000208002301000"
        try:
            for cell in cellsWithDigits:
                cell["label"] = digitPredictor.predictDigit(cell["cell_image"])
            layout = puzzleProcessor.getPuzzleLayout(cellsWithDigits)
        except Exception as e:
            print(e)
        print("Sending layout...")
        self.send_response(201)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes(layout, "utf-8"))

    def randomPuzzleRetrieve(self):
        layout = "000604700706000009000005080070020093800000005430010070050200000300000208002301000"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes(layout, "utf-8"))



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
