import asfapi
import requests
from os import path

# testing folderMake
print("testing folderMake()function")
asfapi.folderMake("./test_folder")
try:
    path.exists("./test_folder")
except:
    print("FAIL - Folder not created")
asfapi.folderMake("./test_folder")
print("If folder aready exists message was printed, then PASS")


# testing getBounds
print("\ntesting getBounds")
# Which tile
tile_num = 1743
# Path to grid shapefile
shapefile = "/mnt/Dados5/PEER_mapping/vectors/SA_grid_50km/grid_PEER_focus.shp"

tile_bbox = asfapi.getBounds(tile_num, shapefile)
if isinstance(tile_bbox, str):
    print(tile_bbox)
    print("PASS")
else:
    print(tile_bbox)
    print("FAIL - Output is not a string")

# testing queryASF
print("\nTesting queryASF no output")

req = asfapi.queryASF(tile_num, shapefile)
if isinstance(req, requests.Response):
    print("PASS")
else:
    print("FAIL")

# print("\nTesting queryASF output")
# req, csv = asfapi.queryASF(tile_num, shapefile, returncsv=True)
# print(csv)

# testting getImages
down_folder = "./test_download"
asfapi.getImages(req, down_folder)
