'''

Solution to Challenge 5 for Geospatial Vision and Visualization

Authors: Arun, Himanshu, Shivani, Suraj

Objective: Given two sets of lat long values, get map tile of region bounded by the inputs, at maximum zoom level.

Overall Approach:
- First we estimate maximum zoom level available, based on the two given inputs.
- Then we get the map tiles based on the estimated maximum zoom level
- If any of the map tile is not available, then we update our zoom level (current-1) and redownload all map tiles at updated zoom level
- At last when all map tiles are available, we stitch them together and display the output   
- Final tile is resized to fit on screen. Original size version is saved to the result folder

'''
# Getting the needed packages
import requests
import json
import cv2
import argparse
import urllib
import numpy as np
from map_utils import *


		
# This function returns a bing map tile, that has the given lat, long
def getMapTile(latitude, longitude, zoomLevel):
	reqUrl = "http://dev.virtualearth.net/REST/V1/Imagery/Metadata/Aerial/%s,%s?zl=%d&o=json&key=" %(latitude, longitude, zoomLevel)
	finalReqUrl = reqUrl + KEY
	response = requests.get(finalReqUrl)
	
	jsonData = json.loads(response.text)
	mapTileUrl = jsonData["resourceSets"][0]["resources"][0]["imageUrl"]

	print "Sit tight while we get your map tile"
	imgResponse = urllib.urlopen(mapTileUrl)
	mapTile = np.asarray(bytearray(imgResponse.read()), dtype="uint8")
	mapTile = cv2.imdecode(mapTile, cv2.IMREAD_COLOR)
	return mapTile



# This function returns a bing map tile, given its QuadKey
def getMapTileWithQuadKey(quadKey):
	mapTileUrl = "http://h0.ortho.tiles.virtualearth.net/tiles/h%s.jpeg?g=131" %(str(quadKey))
	imgResponse = urllib.urlopen(mapTileUrl)
	mapTile = np.asarray(bytearray(imgResponse.read()), dtype="uint8")
	mapTile = cv2.imdecode(mapTile, cv2.IMREAD_COLOR)
	return mapTile



# This function gets the tileX and tileY values, given lat, long and zoom values
def getTileXY(latitude, longitude, zoomLevel):
	latitude = clip(latitude, MIN_LATITUDE, MAX_LATITUDE)
	longitude = clip(longitude, MIN_LONGITUDE, MAX_LONGITUDE)

	sinLatitude = np.sin(latitude * np.pi/180)
	levelConstant = 2**zoomLevel
	pixelX = ((longitude + 180) / 360) * 256 * levelConstant
	pixelY = (0.5 - np.log((1 + sinLatitude) / (1 - sinLatitude)) / (4 * np.pi)) * 256 * levelConstant
	tileX = int(np.floor(pixelX / 256))
	tileY = int(np.floor(pixelY / 256))
	return tileX, tileY



# Given starting and ending tile tuples, this function calculates and returns list of all intermediate tileX,Y values
def getListOfTiles(tile1, tile2):
	tiles = []
	for i in range(tile1[0],tile2[0]+1):
		for j in range(tile1[1],tile2[1]+1):
			tuple = (i, j)
			tiles.append(tuple)
    	return tiles



# Given tileX,Y values and zoom level, this function gets the quad key
def getQuadKey(tileX, tileY, zoomLevel):	
	quadKey = ''
	for i in range(zoomLevel, 0, -1):
		digit = 0
		mask = 1 << (i-1)
		if tileX & mask != 0:
			digit += 1
		if tileY & mask != 0:
			digit += 2
		quadKey += str(digit)
	return quadKey



# Given two sets of lat long values, this function estimates maximum zoom available and gets tileXY list
def getInitialTileXYList(latitude1, longitude1, latitude2, longitude2):	
	zoomLevel = 23
	print "Calculating max zoom level estimate..."
	for itr in range(HIGHEST_ZL,0,-1):	
		sTileX, sTileY = getTileXY(latitude1, longitude1, itr)
		eTileX, eTileY = getTileXY(latitude2, longitude2, itr)

		mapTile3 = getMapTileWithQuadKey(getQuadKey(sTileX, sTileY, itr))
		mapTile4 = getMapTileWithQuadKey(getQuadKey(eTileX, eTileY, itr))

		diff = cv2.absdiff(mapTile3,error)
		if int(np.mean(diff)) < 2:
			continue
		else:
			zoomLevel = itr
			break

	print "Maximum Zoom Level Estimate (based on start and end tiles) : ", zoomLevel

	tileList = getListOfTiles(min((eTileX,eTileY),(sTileX,sTileY)), max((eTileX,eTileY),(sTileX,sTileY)))
	return tileList, zoomLevel



# Given two sets of lat long values and zoom level, this function gets revised tileXY list
def getRevisedTileXYList(latitude1, longitude1, latitude2, longitude2, zoomLevel):	
	sTileX, sTileY = getTileXY(latitude1, longitude1, zoomLevel)
	eTileX, eTileY = getTileXY(latitude2, longitude2, zoomLevel)

	tileList = getListOfTiles(min((eTileX,eTileY),(sTileX,sTileY)), max((eTileX,eTileY),(sTileX,sTileY)))
	return tileList



# This functions downloads individual maptiles using quad keys derived from tileXY values. If any of the maptile is not available, this functions returns
# NOT_OK status message. If all maptiles are good, this functions concatenates them and returns final tile with OK status message 
def getReqMapTile(tileList):
	global sMapTile, eMapTile
	startXVal = tileList[0][0]	
	endYVal = tileList[-1][1]
	IsFirstTile = True	
	colTiles = []
	reqMapTile = []

	print "The map tile you requested is being downloaded..."

	if args["release"] == False:
		sMapTile = getMapTileWithQuadKey(getQuadKey(tileList[0][0], tileList[0][1], zoomLevel))
		eMapTile = getMapTileWithQuadKey(getQuadKey(tileList[-1][0], tileList[-1][1], zoomLevel))

	for i in range(0,len(tileList)):
		xVal = tileList[i][0]
		yVal = tileList[i][1]
		print "Getting tile #%d of %d tiles" %(i+1,len(tileList))
		if xVal == startXVal and IsFirstTile == True:
			mapTile = getMapTileWithQuadKey(getQuadKey(xVal, yVal, zoomLevel))
			IsFirstTile = False
			diff = cv2.absdiff(mapTile,error)
			if int(np.mean(diff)) < 2:
				return reqMapTile, "NOT_OK"			
		elif xVal == startXVal:
			mapTileBelow = getMapTileWithQuadKey(getQuadKey(xVal, yVal, zoomLevel))
			diff = cv2.absdiff(mapTileBelow,error)
			if int(np.mean(diff)) < 2:
				return reqMapTile, "NOT_OK"	
			mapTile = np.concatenate((mapTile,mapTileBelow),axis = 0)
		if yVal == endYVal:
			colTiles.append(mapTile)
			IsFirstTile = True
			startXVal += 1

	for each in colTiles:
		if IsFirstTile == True:
			reqMapTile = each
			IsFirstTile = False
		else:
			reqMapTile = np.concatenate((reqMapTile,each),axis = 1)	

	# resize final image to fit on screen	
	cv2.imwrite("result/resultantTile.jpeg", reqMapTile)	
	reqMapTile = resize_img(reqMapTile,height=512)
	return reqMapTile, "OK"



# Below is the main driving script. As suggested earlier, we first estimate maximum zoom and download tiles. We update zoom and redownload until all tiles 
# are valid. At last, we stitch and present the final map tile.
if __name__ == "__main__":	
	print "** Satellite/Aerial Image Retriever v1.0 **"
	sMapTile = []; eMapTile = []
	# Build the argument parser and split the arguments

	defaultInputSet1 = {"lat1":"41.882692", "long1":"-87.623332", "lat2":"41.883692", "long2":"-87.625332"}

	# Uncomment the below line to test with second set of inputs
	'''
	defaultInputSet1 = {"lat1":"40.714550167322159", "long1":"-74.007124900817871", "lat2":"40.715550167322159", "long2":"-74.009124900817871"}
	'''

	try:
		ap = argparse.ArgumentParser()
		ap.add_argument("-lt1", "--latitude1", default = defaultInputSet1["lat1"],
			help = "Latitude1")
		ap.add_argument("-ln1", "--longitude1", default = defaultInputSet1["long1"],
			help = "Longitude1")
		ap.add_argument("-lt2", "--latitude2", default = defaultInputSet1["lat2"],
			help = "Latitude2")
		ap.add_argument("-ln2", "--longitude2", default = defaultInputSet1["long2"],
			help = "Longitude2")
		ap.add_argument("-r", "--release", default = False,
			help = "debug or release mode")
		# Function vars returns a dictionary that represents a symbol table
		args = vars(ap.parse_args())
		error = cv2.imread("masks/error.jpeg")
	
		tileList, zoomLevel = getInitialTileXYList(float(args["latitude1"]), float(args["longitude1"]), float(args["latitude2"]), float(args["longitude2"]))
		#print tileList
		reqMapTile, statusCode = getReqMapTile(tileList)

		# As long as status code from getReqMapTile is NOT_OK, go down one zoom level and try again
		while(statusCode == "NOT_OK"):
			tileList, zoomLevel = getRevisedTileXYList(float(args["latitude1"]), float(args["longitude1"]), float(args["latitude2"]), \
											float(args["longitude2"]), zoomLevel-1)
			reqMapTile, statusCode = getReqMapTile(tileList)
	
		# Show intermediate results in debug mode
		if args["release"] == False:
			cv2.imshow("MapTile of 1st input", sMapTile)
			cv2.imshow("MapTile of 2nd input", eMapTile)

		cv2.imshow("Requested map tile", reqMapTile)	
		print "The requested map tile (resized) is being displayed"
		print "The original resultant map tile is saved in result folder"
		cv2.waitKey(0)
	except:
		print "ERROR: Unknown -- Please input valid lat long values and follow all instructions"
		

	
