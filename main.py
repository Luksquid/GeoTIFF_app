import random
import numpy as np
import rasterio
from math import floor
from math import ceil
from math import fabs
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
import plotly.graph_objects as go
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog
import sys
import pyproj
sys.setrecursionlimit(2000)

class ScaleRange:

    lRange: float
    rRange: float
    color: str

class FileImage:

    RGBtab: np.ndarray
    GREYtab: np.ndarray
    TIFtab: np.ndarray
    CLtab: np.ndarray
    ListOfScaleRanges = []

    def __init__(self, img):
        with rasterio.open(img) as dataset:
            self.TIFtab = dataset.read(1)
            self.fX, self.fY = dataset.xy(0, 0)
            self.lX, self.lY = dataset.xy(len(self.TIFtab)-1, len(self.TIFtab[0])-1)
            self.epsg = dataset.crs.to_epsg()

        transformer = pyproj.Transformer.from_crs(str(self.epsg), "epsg:4326")
        point = transformer.transform(self.fY, self.fX)
        self.fX = point[0]
        self.fY = point[1]
        point = transformer.transform(self.lY, self.lX)
        self.lX = point[0]
        self.lY = point[1]
        self.GREYtab = self.toGrey().astype(dtype=np.uint8)
        self.RGBtab = self.toRGB().astype(dtype=np.uint8)
        self.distance1 = fabs((self.lX - self.fX) / len(self.TIFtab))
        self.distance2 = fabs((self.fY - self.lY) / len(self.TIFtab))

    def toGrey(self, ranges = False):
        tab = np.copy(self.TIFtab)
        min = np.setdiff1d(tab, [-999]).min()
        max = tab.max()
        compartment = (max - min) / 255

        for x in range(len(tab)):
            for y in range(len(tab[0])):
                if tab[x][y] == -999:
                    tab[x][y] = 0
                else:
                    tab[x][y] = floor((tab[x][y]-min)/compartment)
                if ranges == True:
                    for r in self.ListOfScaleRanges:
                        if self.TIFtab[x][y] >= r[0] and self.TIFtab[x][y] <= r[1]:
                            tab[x][y] = r[2]
        tempList = tab.astype(int)
        return np.stack((tempList, tempList, tempList), axis = 2)

    def toRGB(self, ranges = False):
        tab = self.GREYtab
        RGBtab = np.copy(tab)
        with open('colors.txt', 'r') as colorFile:
            listOfColors = colorFile.readlines()
        colorFile.close()
        for x in range(len(tab)):
            for y in range(len(tab[0])):
                tempColors = listOfColors[int(tab[x][y][0])]
                colorList = tempColors.split(' ', 2)
                RGBtab[x][y] = colorList
                if ranges == True:
                    for r in self.ListOfScaleRanges:
                        if self.TIFtab[x][y] >= r[0] and self.TIFtab[x][y] <= r[1]:
                            RGBtab[x][y] = r[2].split(', ', 2)
        return RGBtab

    def addScaleRange(self, lRange: float, rRange: float, color: str):

        self.ListOfScaleRanges.append([lRange, rRange, color])

    def deleteScaleRange(self, index: int):

        self.ListOfScaleRanges.pop(index)

    def updateScaleRange(self, g, c):
        if(g == True):
            self.GREYtab = self.toGrey(True)
        if(c == True):
            self.RGBtab = self.toRGB(True)

    def heightOfThePixel(self, point):
        return self.TIFtab[point[0]][point[1]]

    def createTheLine(self, point1, point2, c=True, g=True):
        color = [255, 0, 0]
        x1, y1 = point1
        x2, y2 = point2

        dx = x2 - x1
        dy = y2 - y1

        numberOfPoints = max(abs(dx), abs(dy)) + 1
        heights = []

        x_increment = dx / float(numberOfPoints - 1)
        y_increment = dy / float(numberOfPoints - 1)

        linePoints = np.zeros((numberOfPoints , 2), dtype=np.float32)


        for i in range(numberOfPoints):
            x = x1 + i * x_increment
            y = y1 + i * y_increment
            linePoints[i] = [floor(x), floor(y)]
            heights.append(self.TIFtab[floor(x)][floor(y)])
        x = [i for i in range(len(heights))]
        fig = go.Figure(data=go.Scatter(x = x, y = heights))
        fig.update_layout(
            title='Heights',
            xaxis_title='Pixel',
            yaxis_title='Heights'
        )
        fig.show()

        if c==True:
            for p in linePoints.astype(int):
                self.RGBtab[p[0]][p[1]] = color
                try:
                    self.RGBtab[p[0]][p[1]+1] = color
                except:
                    pass
                try:
                    self.RGBtab[p[0]][p[1]-1] = color
                except:
                    pass

        if g==True:
            for p in linePoints.astype(int):
                self.GREYtab[p[0]][p[1]] = color
                try:
                    self.GREYtab[p[0]][p[1]+1] = color
                except:
                    pass
                try:
                    self.GREYtab[p[0]][p[1]-1] = color
                except:
                    pass

    def contourDetection(self):
        arr = self.GREYtab
        layers = np.copy(self.GREYtab)
        for x in range(len(self.GREYtab)):
            for y in range(len(self.GREYtab[0])):
                c = arr[x][y][0]
                try:
                    t = [ arr[x - 1][y][0]!=c, arr[x][y - 1][0] != c, arr[x][y + 1][0] != c, arr[x + 1][y][0] != c,]
                    if(any(t) and x != 0 and y != 0):
                        layers[x][y] = [0, 0, 0]
                    else:
                        layers[x][y] = [255, 255, 255]
                except:
                    layers[x][y] = [0, 0, 0]
        self.CLtab = layers
        for x in range(len(self.GREYtab)):
            for y in range(len(self.GREYtab[0])):
                self.CLtab[len(self.GREYtab)-1][y] = [255, 255, 255]
                self.CLtab[x][len(self.GREYtab[0]) -1] = [255, 255, 255]
        self.GREYtab = self.toGrey(False)

    def contourLine(self, frequency):
        min = self.TIFtab[self.TIFtab != self.TIFtab.min()].min()
        max = self.TIFtab.max()
        tabOfLayers = [i for i in range(100, ceil(max), frequency)]
        self.tabOfLayers = tabOfLayers
        tabOfColors = [i for i in range(0, 255, ceil(255/(len(tabOfLayers))))]
        for i in range(len(tabOfLayers)):
            if(i != len(tabOfLayers)-1):
                self.addScaleRange(tabOfLayers[i], tabOfLayers[i+1], tabOfColors[i])
            else:
                self.addScaleRange(tabOfLayers[i], max, tabOfColors[i])
        self.updateScaleRange(g=True, c=False)
        self.contourDetection()

    lines = []
    line = []
    color = [255, 0, 0]


    def toGeo(self):
        for x in range(len(self.lines)):
            for y in range(len(self.lines[x])):
                point = self.lines[x][y]
                point = [self.fX-(self.distance1*point[0]), self.fY+(self.distance2*point[1]), self.TIFtab[point[0]][point[1]]]
                self.lines[x][y] = point

    def addToLine(self, point):
        hm = 0

        self.CLtab[point[0]][point[1]] = self.color
        try:
            if self.CLtab[point[0]][point[1] + 1][0] == 0 and point[1] != (len(self.CLtab[1]) - 1):
                if point not in self.line:
                    self.line.append(point)
                self.addToLine([point[0], point[1] + 1])
                hm += 1
        except:
            pass
        try:
            if self.CLtab[point[0] + 1][point[1]][0] == 0 and point[0] != (len(self.CLtab[0]) - 1):
                if point not in self.line:
                    self.line.append(point)
                self.addToLine([point[0] + 1, point[1]])
                hm += 1
        except:
            pass
        try:
            if self.CLtab[point[0] - 1][point[1]][0] == 0 and point[0] != 0:
                if point not in self.line:
                    self.line.append(point)
                self.addToLine([point[0] - 1, point[1]])
                hm += 1
        except:
            pass
        try:
            if self.CLtab[point[0]][point[1] - 1][0] == 0 and point[1] != 0:
                if point not in self.line:
                    self.line.append(point)
                self.addToLine([point[0], point[1] - 1])
                hm += 1
        except:
            pass
        try:
            if self.CLtab[point[0] - 1][point[1] - 1][0] == 0 and point[1] != 0 and point[0] != 0:
                if point not in self.line:
                    self.line.append(point)
                self.addToLine([point[0] - 1, point[1] - 1])
                hm += 1
        except:
            pass
        try:
            if self.CLtab[point[0] - 1][point[1] + 1][0] == 0 and point[0] != 0 and point[1] != (len(self.CLtab[1]) - 1):
                if point not in self.line:
                    self.line.append(point)
                self.addToLine([point[0] - 1, point[1] + 1])
                hm += 1
        except:
            pass
        try:
            if self.CLtab[point[0] + 1][point[1] - 1][0] == 0 and point[1] != 0 and point[0] != (len(self.CLtab[0]) - 1):
                if point not in self.line:
                    self.line.append(point)
                self.addToLine([point[0] + 1, point[1] - 1])
                hm += 1
        except:
            pass
        try:
            if self.CLtab[point[0] + 1][point[1] + 1][0] == 0 and point[1] != (len(self.CLtab[1]) - 1) and point[0] != (len(self.CLtab[0]) - 1):
                if point not in self.line:
                    self.line.append(point)
                self.addToLine([point[0] + 1, point[1] + 1])
                hm += 1

        except:
            pass
        if hm==0:
            self.lines.append(self.line)
            self.line = []
            self.color = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]

    def readLines(self):
        map = np.copy(self.CLtab)
        for x in range(len(self.CLtab)):
            for y in range(len(self.CLtab[0])):
                point = [x, y]
                if(self.CLtab[x][y][0]==0):
                    self.addToLine(point)
        self.CLtab = map

    def toKml(self, location: str,):
        with open(location + '/ContourLines.kml', 'w') as kmlFile:
            kmlFile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            kmlFile.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
            kmlFile.write('    <Document>\n')
            kmlFile.write('        <Style id="blueLineStyle">\n')
            kmlFile.write('            <LineStyle>\n')
            kmlFile.write('                <color>ff0000ff</color>\n')
            kmlFile.write('                <width>2.00</width>\n')
            kmlFile.write('            </LineStyle>\n')
            kmlFile.write('        </Style>\n')
            for x in range(len(self.lines)):
                height = ''
                try:
                    height = float(self.lines[x][0][2])
                except:
                    height2 = ''
                if height!='':
                    for layerIndex in range(len(self.tabOfLayers)):
                        if float(height) < self.tabOfLayers[0]:
                            height2 = str(self.tabOfLayers[0])
                        elif float(height) >= self.tabOfLayers[len(self.tabOfLayers) - 1]:
                            print(float(height), self.tabOfLayers[len(self.tabOfLayers) - 1])
                            height2 = str(self.tabOfLayers[len(self.tabOfLayers) - 1])
                        elif float(height) >= self.tabOfLayers[layerIndex] and float(height) < self.tabOfLayers[layerIndex + 1]:
                            height2 = str(self.tabOfLayers[layerIndex + 1])
                kmlFile.write('        <Placemark>\n')
                kmlFile.write('            <name>' + height2 + '</name>\n')
                kmlFile.write('            <styleUrl>#blueLineStyle</styleUrl>\n')
                kmlFile.write('            <LineString>\n')
                kmlFile.write('                <coordinates>\n')
                for y in range(len(self.lines[x])):
                    point = self.lines[x][y]
                    kmlFile.write('                    ' + str(round(point[1], 6)) + ',' + str(round(point[0], 6)) + ',' + str(round(float(point[2]), 2)) + '\n')
                kmlFile.write('                </coordinates>\n')
                kmlFile.write('            </LineString>\n')
                kmlFile.write('        </Placemark>\n')
            kmlFile.write('    </Document>\n')
            kmlFile.write('</kml>\n')




class ImageWindow:
    def __init__(self, image: FileImage):

        self.buttonWidth = 12
        self.buttonHeiht = 1
        self.entryWidth = 13
        self.padx = 10
        self.pady = 10
        self.sticky = 'w'
        self.even = True
        self.image = image
        self.image_array = image.RGBtab
        self.grey = False
        self.window_title = "Aplikacja do plików TIF"

        self.root = tk.Tk()
        self.root.resizable(False, False)
        self.root.title(self.window_title)
        self.root.wm_minsize()

        self.figure = plt.figure(figsize=(9, 9), dpi=80)
        self.ax = self.figure.add_subplot(111)
        self.ax.imshow(self.image_array)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.root)
        self.toolbar.update()
        self.toolbar.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.newTifButton = tk.Button(self.button_frame, command=self.newTif, text="New tif", width=self.buttonWidth, height=self.buttonHeiht)
        self.newTifButton.grid(row=0, column=0, padx=self.padx, pady=self.pady)

        self.resetButton = tk.Button(self.button_frame, command=self.reset, text="Reset", width=self.buttonWidth, height=self.buttonHeiht)
        self.resetButton.grid(row=0, column=1, padx=self.padx, pady=self.pady, sticky='e')

        self.colorButton = tk.Button(self.button_frame, text="Color", command=self.changeColor, width=self.buttonWidth, height=self.buttonHeiht)
        self.colorButton.grid(row=0, column=2, padx=self.padx, pady=self.pady)

        self.scalesButton = tk.Button(self.button_frame, text="Scales", command=self.scalesMenu, width=self.buttonWidth, height=self.buttonHeiht)
        self.scalesButton.grid(row=0, column=3, padx=self.padx, pady=self.pady)

        self.heightProfile = tk.Button(self.button_frame, text="Height profile", command=self.createTheLine, width=self.buttonWidth, height=self.buttonHeiht)
        self.heightProfile.grid(row=0, column=4, padx=self.padx, pady=self.pady)

        self.contourLines = tk.Button(self.button_frame, text="Contour lines", command=self.contourLinesMenu, width=self.buttonWidth, height=self.buttonHeiht)
        self.contourLines.grid(row=0, column=5, padx=self.padx, pady=self.pady)

        self.pixelLabel = tk.Label(self.button_frame, text="Pixel height")
        self.pixelLabel.grid(row=1, column=0, padx=self.padx, pady=self.pady)

        self.pixelHeight = tk.Entry(self.button_frame, width=25)
        self.pixelHeight.grid(row=1, column=1, padx=self.padx, pady=self.pady)

        self.cancel_button = tk.Button(self.button_frame, text="Cancel", command=self.button_frame.quit, width=self.buttonWidth, height=self.buttonHeiht)
        self.cancel_button.grid(row=1, column=5, padx=self.padx, pady=self.pady)

        self.canvas.mpl_connect("button_press_event", self.on_canvas_click)

    def on_canvas_click(self, event):
        x, y = event.xdata, event.ydata
        try:
            x = int(x)
            y = int(y)
            if x >= 0 and y >= 0 and x < self.image_array.shape[1] and y < self.image_array.shape[0]:
                pixel_value = self.image_array[y, x]
                self.pixelHeight.delete(0, tk.END)
                self.pixelHeight.insert(tk.END,  f"{self.image.TIFtab[y][x]}")
                point = y, x
                if(self.even==True):
                    self.firstPoint = point
                    self.even = False
                else:
                    self.secondPoint = point
                    self.even = True
        except:
            pass

    def errorFunction(self, comunicate: str, sizeOfTheWindow: str):
        popupWidow = tk.Tk()
        popupWidow.geometry(sizeOfTheWindow)
        popupWidow.title(comunicate)
        padding = 10
        popupWidow.resizable(False, False)
        errorLabel = tk.Label(popupWidow, text=comunicate)
        errorLabel.grid(row=0, column=0, padx=padding, pady=padding)
        ok_button = tk.Button(popupWidow, text="Ok", command=popupWidow.destroy, height=1, width=6)
        ok_button.grid(row=1, column=0, padx=padding, pady=padding)

    def newTif(self):
        def openFile():
            folder_path = filedialog.askopenfilename()
            path_entry.delete(0, tk.END)
            path_entry.insert(tk.END, folder_path)

        def submit():
            try:
                filePath = path_entry.get()
                image = FileImage(filePath)
                imageWindow = ImageWindow(image)
                window.destroy()
            except rasterio.errors.RasterioIOError:
                popupWidow = tk.Tk()
                popupWidow.geometry("90x90")
                popupWidow.title("Comunicate")
                padding = 10
                popupWidow.resizable(False, False)
                errorLabel = tk.Label(popupWidow, text="Wrong path")
                errorLabel.grid(row=0, column=0, padx=padding, pady=padding)
                ok_button = tk.Button(popupWidow, text="Ok", command=popupWidow.destroy, height=1, width=6)
                ok_button.grid(row=1, column=0, padx=padding, pady=padding)

        window = tk.Tk()
        window.geometry("490x120")
        window.title("Aplikacja do plików TIF")
        buttonWidth = 6
        buttonHeiht = 1

        browse_button = tk.Button(window, text="Browse", command=openFile, height=buttonHeiht, width=buttonWidth)
        browse_button.grid(row=0, column=2, padx=10, pady=10)

        path_entry = tk.Entry(window, width=53)
        path_entry.grid(row=0, column=1)

        submit_button = tk.Button(window, text="Run", command=submit, height=buttonHeiht, width=buttonWidth)
        submit_button.grid(row=3, column=1, pady=10, sticky=tk.E)

        cancel_button = tk.Button(window, text="Cancel", command=window.quit, height=buttonHeiht, width=buttonWidth)
        cancel_button.grid(row=3, column=2)

        label1 = tk.Label(window, text="Input")
        label1.grid(row=0, column=0, padx=25, pady=10)

    def fileLoading(self):
        newTif = FileImage(self.newTifButton.get())
        self.image = newTif
        self.image_array = self.image.RGBtab
        self.ax.imshow(self.image_array)
        self.canvas.draw()

    def forgetAll(self):
        self.newTifButton.grid_forget()
        self.resetButton.grid_forget()
        self.colorButton.grid_forget()
        self.scalesButton.grid_forget()
        self.heightProfile.grid_forget()
        self.contourLines.grid_forget()
        self.pixelLabel.grid_forget()
        self.pixelHeight.grid_forget()
        self.cancel_button.grid_forget()

    def displayMainMenu(self):
        self.newTifButton.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        self.resetButton.grid(row=0, column=1, padx=self.padx, pady=self.pady, sticky='e')
        self.colorButton.grid(row=0, column=2, padx=self.padx, pady=self.pady)
        self.scalesButton.grid(row=0, column=3, padx=self.padx, pady=self.pady)
        self.heightProfile.grid(row=0, column=4, padx=self.padx, pady=self.pady)
        self.contourLines.grid(row=0, column=5, padx=self.padx, pady=self.pady)
        self.pixelLabel.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.pixelHeight.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        self.cancel_button.grid(row=1, column=5, padx=self.padx, pady=self.pady)

    def scalesGoBack(self):
        self.goBack.grid_forget()
        self.startOfTheScaleLabel.grid_forget()
        self.startOfTheScaleInput.grid_forget()
        self.endOfTheScaleLabel.grid_forget()
        self.endOfTheScaleInput.grid_forget()
        self.colorLabel.grid_forget()
        self.colorInput.grid_forget()
        self.addScaleCommitButton.grid_forget()
        try:
            self.colorOfScaleLabel.grid_forget()
            self.deleteScaleCommitButton.grid_forget()
            self.colorOfScaleList.grid_forget()
        except:
            pass
        self.displayMainMenu()

    def scalesMenu(self):
        self.forgetAll()

        self.goBack = tk.Button(self.button_frame, command=self.scalesGoBack, text="Back", width=self.buttonWidth, height=self.buttonHeiht)
        self.goBack.grid(row=0, column=0, padx=self.padx, pady=self.pady)

        self.startOfTheScaleLabel = tk.Label(self.button_frame, text="Start of the scale")
        self.startOfTheScaleLabel.grid(row=1, column=0, padx=self.padx, pady=self.pady)

        self.startOfTheScaleInput = tk.Entry(self.button_frame, width=self.entryWidth)
        self.startOfTheScaleInput.grid(row=1, column=1, padx=self.padx, pady=self.pady)

        self.endOfTheScaleLabel = tk.Label(self.button_frame, text="End of the scale")
        self.endOfTheScaleLabel.grid(row=1, column=2, padx=self.padx, pady=self.pady)

        self.endOfTheScaleInput = tk.Entry(self.button_frame, width=self.entryWidth)
        self.endOfTheScaleInput.grid(row=1, column=3, padx=self.padx, pady=self.pady)

        self.colorLabel = tk.Label(self.button_frame, text="Color")
        self.colorLabel.grid(row=1, column=4, padx=self.padx, pady=self.pady)

        self.colorInput = tk.Entry(self.button_frame, width=self.entryWidth)
        self.colorInput.grid(row=1, column=5, padx=self.padx, pady=self.pady)

        self.addScaleCommitButton = tk.Button(self.button_frame, command=self.addRange, text="Add", width=self.buttonWidth, height=self.buttonHeiht)
        self.addScaleCommitButton.grid(row=1, column=6, padx=self.padx, pady=self.pady)

        self.listOfTheCollors = []


    def contourLinesGoBack(self):
        self.goBack.grid_forget()
        self.contourLinesLabel.grid_forget()
        self.contourLinesInput.grid_forget()
        self.contourLinesCommit.grid_forget()
        self.contourLinesSaveEntry.grid_forget()
        self.contourLinesSaveSubmitButton.grid_forget()
        self.contourLinesSaveBrowseButton.grid_forget()
        self.contourLinesSaveLabel.grid_forget()
        self.displayMainMenu()

    def contourLinesMenu(self):
        self.forgetAll()

        self.goBack = tk.Button(self.button_frame, command=self.contourLinesGoBack, text="Back", width=self.buttonWidth, height=self.buttonHeiht)
        self.goBack.grid(row=0, column=0, padx=self.padx, pady=self.pady)

        self.contourLinesLabel = tk.Label(self.button_frame, text="Contour lines frequency")
        self.contourLinesLabel.grid(row=1, column=0, padx=self.padx, pady=self.pady)

        self.contourLinesInput = tk.Entry(self.button_frame, width=self.entryWidth)
        self.contourLinesInput.grid(row=1, column=1, padx=self.padx, pady=self.pady)

        self.contourLinesCommit = tk.Button(self.button_frame, text="Generate", command=self.DisplayContourLines, width=self.buttonWidth, height=self.buttonHeiht)
        self.contourLinesCommit.grid(row=1, column=2, padx=self.padx, pady=self.pady, sticky='w')

        self.contourLinesSaveLabel = tk.Label(self.button_frame, text="Export contour lines to KML file")
        self.contourLinesSaveLabel.grid(row=2, column=0, padx=self.padx, pady=self.pady)

        self.contourLinesSaveEntry = tk.Entry(self.button_frame, width=53)
        self.contourLinesSaveEntry.grid(row=2, column=2, padx=self.padx, pady=self.pady)

        def openDir():
            self.button_frame.update_idletasks()
            folderPath = filedialog.askdirectory()
            self.contourLinesSaveEntry.delete(0, tk.END)
            self.contourLinesSaveEntry.insert(tk.END, folderPath)

        def submit():
            try:
                self.image.readLines()
                self.image.toGeo()
                try:
                    filePath = self.contourLinesSaveEntry.get()
                    self.image.toKml(filePath)
                except:
                    self.errorFunction("Wrong path", "90x90")
            except:
                self.errorFunction("Contour lines have to be generated first", "250x90")



        self.contourLinesSaveBrowseButton = tk.Button(self.button_frame, text="Browse", command=openDir, height=self.buttonHeiht, width=self.buttonWidth)
        self.contourLinesSaveBrowseButton.grid(row=2, column=1, padx=self.padx, pady=self.pady)

        self.contourLinesSaveSubmitButton = tk.Button(self.button_frame, text="Save", command=submit, height=self.buttonHeiht, width=self.buttonWidth)
        self.contourLinesSaveSubmitButton.grid(row=2, column=3, sticky=tk.E, padx=self.padx, pady=self.pady)

    def changeColor(self):
        if(self.grey==False):
            self.image.ListOfScaleRanges = []
            self.image_array = self.image.GREYtab
            self.ax.imshow(self.image_array)
            self.canvas.draw()
            self.grey = True
        elif(self.grey==True):
            self.image.ListOfScaleRanges = []
            self.image_array = self.image.RGBtab
            self.ax.imshow(self.image_array)
            self.canvas.draw()
            self.grey = False

    def reset(self):
        self.image.GREYtab = self.image.toGrey()
        self.image.RGBtab = self.image.toRGB()
        self.firstPoint = ''
        self.secondPoint = ''
        if(self.grey==True):
            self.image_array = self.image.GREYtab
            self.ax.imshow(self.image_array)
            self.canvas.draw()
        else:
            self.image_array = self.image.RGBtab
            self.ax.imshow(self.image_array)
            self.canvas.draw()
        self.pixelHeight.delete(0, tk.END)

    def addRange(self):

        try:
            start = float(self.startOfTheScaleInput.get())
            end = float(self.endOfTheScaleInput.get())
            if end >= start:
                color = self.colorInput.get()
                isRGB = ''
                if self.grey == False:
                    try:
                        colorList = color.split(', ', 2)
                        colorList = [ int(i) for i in colorList ]
                        isRGB = colorList[0]>=0 and colorList[0]<=255 and colorList[1]>=0 and colorList[1]<=255 and colorList[2]>=0 and colorList[2]<=255
                    except:
                        self.errorFunction("Color should be in rgb format", "190x90")
                else:
                    try:
                        color = int(color)
                        isRGB = color>=0 and color<=255
                    except:
                        self.errorFunction("Color should be an integer", "170x90")
                if(isRGB):
                    self.image.addScaleRange(start, end, color)
                    self.listOfTheCollors = [row[2] for row in self.image.ListOfScaleRanges]
                    if(self.grey==False):
                        self.image_array = self.image.toRGB(True)
                        self.ax.imshow(self.image_array)
                        self.canvas.draw()
                    else:
                        self.image_array = self.image.toGrey(True)
                        self.ax.imshow(self.image_array)
                        self.canvas.draw()

                    self.colorOfScaleLabel = tk.Label(self.button_frame, text="Color")
                    self.colorOfScaleLabel.grid(row=2, column=0, padx=self.padx, pady=self.pady)
                    self.colorOfScaleList = tk.ttk.Combobox(self.button_frame, values=self.listOfTheCollors, width=20)
                    self.colorOfScaleList.grid(row=2, column=2, padx=self.padx, pady=self.pady)
                    self.deleteScaleCommitButton = tk.Button(self.button_frame, command=self.removeRange, text="Delete", width=self.buttonWidth, height=self.buttonHeiht)
                    self.deleteScaleCommitButton.grid(row=2, column=3, padx=self.padx, pady=self.pady)
                    self.startOfTheScaleInput.delete(0, tk.END)
                    self.endOfTheScaleInput.delete(0, tk.END)
                    self.colorInput.delete(0, tk.END)
                    self.colorOfScaleList.delete(0, tk.END)
            else:
                self.errorFunction("End of the scale should be bigger than start of the scale", "320x100")
        except ValueError:
            try:
                tempStart = float(self.startOfTheScaleInput.get())
                tempEnd = float(self.endOfTheScaleInput.get())
            except:
                self.errorFunction("Start of the scale and end of the scale should be a floating point number.\n Any field can be empty", "400x100")

    def removeRange(self):
        value = self.colorOfScaleList.get()
        self.image.ListOfScaleRanges = [row for row in self.image.ListOfScaleRanges if value not in row]
        if(self.grey==False):
            self.image_array = self.image.toRGB(True)
            self.ax.imshow(self.image_array)
            self.canvas.draw()
        else:
            self.image_array = self.image.toGrey(True)
            self.ax.imshow(self.image_array)
            self.canvas.draw()


    def createTheLine(self):
        try:
            self.image.createTheLine(self.firstPoint, self.secondPoint)
            self.ax.imshow(self.image_array)
            self.canvas.draw()
        except:
            self.errorFunction("To create a line, mark its beginning and end by clicking", "320x90")

    def DisplayContourLines(self):
        tempFrequency = self.contourLinesInput.get()
        try:
            frequency = int(self.contourLinesInput.get())
            self.image.contourLine(frequency)
            self.image_array = self.image.CLtab
            self.ax.imshow(self.image_array)
            self.canvas.draw()
        except:
            if tempFrequency == '':
                self.errorFunction("Field can not be empty", "150x90")
            else:
                self.errorFunction("Field must be an integer", "150x90")

    def run(self):
        self.root.mainloop()

def openFile():
    folder_path = filedialog.askopenfilename()
    path_entry.delete(0, tk.END)
    path_entry.insert(tk.END, folder_path)

def submit():
    try:
        filePath = path_entry.get()
        image = FileImage(filePath)
        imageWindow = ImageWindow(image)
        window.destroy()
    except rasterio.errors.RasterioIOError:
        popupWidow = tk.Tk()
        popupWidow.geometry("90x90")
        popupWidow.title("Comunicate")
        padding = 10
        popupWidow.resizable(False, False)
        errorLabel = tk.Label(popupWidow, text="Wrong path")
        errorLabel.grid(row=0, column=0, padx=padding, pady=padding)
        ok_button = tk.Button(popupWidow, text="Ok", command=popupWidow.destroy, height=1, width=6)
        ok_button.grid(row=1, column=0, padx=padding, pady=padding)

window = tk.Tk()
window.geometry("490x120")
window.title("Aplikacja do plików TIF")
buttonWidth = 6
buttonHeiht = 1

browse_button = tk.Button(window, text="Browse", command=openFile, height= buttonHeiht, width=buttonWidth)
browse_button.grid(row=0, column=2, padx=10, pady=10)

path_entry = tk.Entry(window, width=53)
path_entry.grid(row=0, column=1)

submit_button = tk.Button(window, text="Run", command=submit, height= buttonHeiht, width=buttonWidth)
submit_button.grid(row=3, column=1, pady=10, sticky=tk.E)

cancel_button = tk.Button(window, text="Cancel", command=window.quit, height= buttonHeiht, width=buttonWidth)
cancel_button.grid(row=3, column=2)

label1 = tk.Label(window, text="Input")
label1.grid(row=0, column=0, padx=25, pady=10)

window.mainloop()