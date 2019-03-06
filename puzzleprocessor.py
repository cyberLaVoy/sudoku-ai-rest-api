import cv2
import numpy as np

MAX_IMG_DIMENSION = 650     # the maximum dimension of an incoming image
FINAL_CELL_DIMENSION = 28   # final side length for each returned cell
NUM_CORNERS = 850           # number of corners to detect when searching for outer corners of boxes
DIGIT_DETECTION_ZOOM = 7    # amount of zoom on digit, to dismiss cell border lines
DISPLAY_FOR_INSPECTION = False

class PuzzleProcessor:
    def __init__(self, sudokuPuzzleImageBytes):
        self.mSudokuPuzzle = self.loadAndFormatImage(sudokuPuzzleImageBytes) 

    def displayImage(self, title, image):
        cv2.imshow(title, image)
        cv2.waitKey(1)
        input()
        cv2.destroyAllWindows()

    def loadAndFormatImage(self, bytesString):
        print(len(bytesString))
        img = cv2.imdecode(np.frombuffer(bytesString, np.uint8), cv2.IMREAD_GRAYSCALE)
        print("Initial image dimensions:", img.shape)
        if img.shape[0] < img.shape[1]:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE) 
        img = self.shrinkImage(img)
        return img

    def shrinkImage(self, img, maxDimension=MAX_IMG_DIMENSION):
        height, width = img.shape
        scaleFactor = 1
        if height > maxDimension or width > maxDimension:
            scaleFactor = 1/(max(height, width)/maxDimension)
            print("Maximum dimension exceeded.", "scaled height:", height*scaleFactor, "scaled width:", width*scaleFactor)
        return cv2.resize(img,None,fx=scaleFactor, fy=scaleFactor, interpolation = cv2.INTER_AREA)

    def findPointInLargestBlob(self, img):
        maximumArea = -1
        maxPt = (0,0)
        rows, cols = img.shape
        temp = img[0:rows,0:cols].copy() # make a copy of image as to not modify original image
        y = rows//2 
        row = temp[y]         # find the middle row
        for x in range(cols): # scan across middle row
            if row[x] >= 255: 
                mask = np.zeros((rows+2,cols+2), np.uint8)
                cv2.floodFill(temp, mask, (x,y), 42) # 42 is an arbitrary fill in color
                area = np.sum(mask)
                if area > maximumArea:
                    maxPt = (x,y)
                    maximumArea = area
        return maxPt

    def findLargestBlob(self, img):
        pointInOuterGrid = self.findPointInLargestBlob(img)
        rows,cols = img.shape
        mask = np.zeros((rows+2,cols+2), np.uint8)
        boxColor = 25 # a local arbitrary value
        cv2.floodFill(img, mask, pointInOuterGrid, boxColor)                 # fill in blob with arbitrary color value
        retval, img = cv2.threshold(img, boxColor, 0, cv2.THRESH_TOZERO_INV) # remove all color that is not the current blob color
        retval, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY)          # set blob color to white
        kernal = np.ones((2,2), np.uint8)
        img = cv2.dilate(img, kernal, iterations = 2) # dilate to make lines more connected
        return img

    def findCorners(self, img, numCorners=NUM_CORNERS):
        gray = np.float32(img) # to satisfy the corner detection algorithm
                                        # image, maxCorners, qualityLevel, minDistance
        corners = cv2.goodFeaturesToTrack(gray, numCorners, .01, 5)
        corners = np.int0(corners)
        corners = np.array( [corner[0] for corner in corners] )
        return corners

    def outerCorners(self, pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def fourPointTransform(self, image, rect):
        (tl, tr, br, bl) = rect
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        dst = np.array([[0, 0],
                        [maxWidth - 1, 0],
                        [maxWidth - 1, maxHeight - 1],
                        [0, maxHeight - 1]], dtype = "float32")
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        return warped

    def revealDigitOnly(self, img, thresh):
        img = img + 1
        thresh = cv2.bitwise_not(thresh)
        img = cv2.bitwise_and(img, thresh)
        img[img == 0] = 255
        return img

    def centerCellWithDigit(self, img, finalSize=FINAL_CELL_DIMENSION):
        kernal = np.ones((3,3), np.uint8)
        img = cv2.erode(img, kernal, iterations = 2)
        retval, thresh = cv2.threshold(img, np.mean(img)-np.std(img), 255, cv2.THRESH_BINARY) 
        thresh = cv2.copyMakeBorder(thresh, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=255) # disconnect digits that touch the outer edges of cell 
        thresh = cv2.copyMakeBorder(thresh, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=0) # draw outer boder to ensure that the largest contour is the contour of the entire cell 
        img = cv2.copyMakeBorder(img, 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=255) # keep original image the same size as the threshold image
        contours, h = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours.sort(key=cv2.contourArea, reverse=True)
        cv2.drawContours(thresh, contours, -1, 0, 4) # highlight area around digit
        #self.displayImage("Cell", img)
        x, y, w, h = cv2.boundingRect(contours[1])
        #cv2.rectangle(img, (x,y), (x+w,y+h), 0, 5) 
        crop = img[y:y+h,x:x+w]
        thresh = thresh[y:y+h,x:x+w]
        crop = self.revealDigitOnly(crop, thresh)
        scaleFactor = 1/(max(w, h)/finalSize)
        crop = cv2.resize(crop, (0,0), fx=scaleFactor, fy=scaleFactor) 
        sidesBorder = (finalSize - crop.shape[1])/2
        topBottomBorder = (finalSize - crop.shape[0])//2
        offset = 0
        if sidesBorder > int(sidesBorder):
            offset = 1
        sidesBorder = int(sidesBorder)
        crop = cv2.copyMakeBorder(crop, topBottomBorder, topBottomBorder, sidesBorder+offset, sidesBorder, cv2.BORDER_CONSTANT, value=255)
        return crop

    def focusImage(self, img):
        temp = img.copy()
        temp = 255 * ( (temp-np.amin(temp)) / (np.amax(temp)-np.amin(temp)) )
        temp = temp.astype(np.uint8)
        return temp

    def isBlankCell(self, cell, zoomBorder=DIGIT_DETECTION_ZOOM):
        cell = cell[zoomBorder:cell.shape[0]-zoomBorder,zoomBorder:cell.shape[1]-zoomBorder]
        cell = cv2.resize(cell, (0,0), fx=7, fy=7) 
        kernal = np.ones((11,11), np.uint8)
        # remove an outlying color in a group of pixels
        cell = cv2.erode(cell, kernal, iterations = 3)
        if( np.var(cell) > np.mean(cell)):
            return False
        return True

    def extractCellsWithDigits(self, innerBox, boxIndex, cellSidesLength=FINAL_CELL_DIMENSION):
        digits = []
        rows, cols = innerBox.shape
        cellHeight = rows//3
        cellWidth = cols//3
        for i in range(3):
            y1 = i*cellHeight
            y2 = cellHeight+y1
            for j in range(3):
                x1 = j*cellWidth
                x2 = cellWidth+x1
                roi = innerBox[y1:y2,x1:x2]
                if not self.isBlankCell(roi):
                    roi = cv2.resize(roi, (0,0), fx=5, fy=5) 
                    roi = self.focusImage(roi)
                    roi = self.centerCellWithDigit(roi)
                    #self.displayImage("Cell", roi)
                    roi = roi.flatten()
                    digit = {"box_index": boxIndex, "cell_index": 3*i+j, "cell_image": roi, "cell_shape": (cellSidesLength, cellSidesLength)}
                    digits.append(digit)
        return digits

    def findSquareCorners(self, img):
        corners = self.findCorners(img)
        square = self.outerCorners(corners)
        return square

    def findPointInEachInnerbox(self, outerbox):
        rows, cols = outerbox.shape
        boxCoordinates = []
        for y in range(int((rows/3)/2), rows, int(rows/3)):
            for x in range(int((cols/3)/2), cols, int(cols/3)):
                boxCoordinates.append((x,y))
        return boxCoordinates

    def findInnerBoxes(self, outerbox, orignial):
        innerBoxes = []
        boxCoordinates = self.findPointInEachInnerbox(outerbox)
        rows, cols = outerbox.shape
        temp = outerbox[0:rows,0:cols].copy()
        for coor in boxCoordinates:
            mask = np.zeros((rows+2,cols+2), np.uint8)
            cv2.floodFill(temp, mask, coor, 255)
            temp = cv2.bitwise_xor(outerbox, temp)
            kernal = np.ones((3,3), np.uint8)
            temp = cv2.dilate(temp, kernal, iterations = 2) # dilate to grab more area of inner box
            square = self.findSquareCorners(temp)
            innerBox = self.fourPointTransform(orignial, square)
            if DISPLAY_FOR_INSPECTION:
                self.displayImage("innerBox", innerBox) # for examination purposes
            innerBoxes.append(innerBox)
            temp = outerbox[0:rows,0:cols].copy()
        return np.array(innerBoxes)

    def preprocessImage(self, img):
        outerbox = self.focusImage(img)
        outerbox = cv2.GaussianBlur(outerbox, (17,17), 0)
        outerbox = self.focusImage(outerbox)
        if DISPLAY_FOR_INSPECTION:
            self.displayImage("Preprocessing", outerbox) # for examination purposes
        outerbox = cv2.adaptiveThreshold(outerbox, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 17, 2)
        return outerbox

    def fillOuterEdges(self, img):
        temp = cv2.copyMakeBorder(img, 3, 3, 3, 3, cv2.BORDER_CONSTANT, value=255)
        return temp

    def extractDigitContainingCells(self):
        outerbox = self.preprocessImage(self.mSudokuPuzzle)
        outerbox = self.findLargestBlob(outerbox)
        square = self.findSquareCorners(outerbox)
        sudokuBoard = self.fourPointTransform(self.mSudokuPuzzle, square)
        outerbox = self.fourPointTransform(outerbox, square)
        outerbox = self.fillOuterEdges(outerbox) # in case an outer edge of the outer box was cut off
        contours, h = cv2.findContours(outerbox, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(outerbox, contours, -1, 255, 2)
        sudokuBoard = self.fillOuterEdges(sudokuBoard) # make sudoku board img the same size as the outerbox img
        if DISPLAY_FOR_INSPECTION:
            self.displayImage("SudokuBoard",sudokuBoard)
            self.displayImage("OuterBox",outerbox)
        innerBoxes = self.findInnerBoxes(outerbox, sudokuBoard)
        cells = []
        for i in range(len(innerBoxes)):
            cells += self.extractCellsWithDigits(innerBoxes[i], i)
        return np.array(cells)
    
    def getPuzzleLayout(self, labeledCells):
        layout = ['0']*81
        for cell in labeledCells:
            row = 3*(cell["box_index"]//3) + cell["cell_index"]//3
            col = 3*(cell["box_index"]%3) + cell["cell_index"]%3
            layout[9*row+col] = cell["label"]
        layoutStr = ""
        for l in layout:
            layoutStr += l
        return layoutStr