# Downloads PALSAR images from ASF using the API

### Import modules
import pandas as pd  # for manipulating tile and image information
import geopandas  # for reading tile index shapefile
import os  # for folder creation and sending commands to terminal
import requests  # for sending queries to ASF API
import io  # for decoding image list requested from ASF
import glob  # for general file listing
from os import path  # for path manipulation
import re  # for regular expreession operations on strings

###############################################
######## SET NECESSARY PATHS HERE  ############
###############################################

### Base directory for tile folders
basedir = "/mnt/Dados5/PEER_mapping/rasters/Amazon_tiles/"

# Path to grid dataframe
tile_index_path = "/mnt/Dados5/PEER_mapping/vectors/SA_grid_50km/grid_PEER_focus.shp"
# misstile_index_path = '/mnt/Dados5/PEER_mapping/rasters/missing_tiles.csv'

##############################################
##############################################

### Defining custom functions

# Fun to check if dir exists and create it if not
def foldermake(name):
    if not os.path.exists(name):
        os.makedirs(name)
        print("Creating folder " + name)
    else:
        print("Folder " + name + " already exists!")


############## PROCESSING STEPS START HERE ################

# Get tiles shapefile as geopandas dataframe
tiles = pd.DataFrame(geopandas.read_file(tile_index_path)).set_index("tile_num")
# misstiles = pd.read_csv(misstile_index_path)

# Make a global previews folder in the global folders
glob_prev = basedir + "tile_previews/"
if not os.path.exists(glob_prev):
    os.makedirs(glob_prev)

############## PROCESSING STEPS START HERE ################
tilecount = 1
# mtiles = misstiles.tile_num.tolist()
mtiles = tiles.index.tolist()  # iloc[801:,:]


def meetsCondition(element):
    return bool(element > 1990)


subtiles = list(filter(meetsCondition, mtiles))

tiletot = len(subtiles)  # -len(skiptiles)

# tile = 1399


# set downloads folder
down_folder = basedir + "downloads/"
print("#### Setting downloads folder to " + down_folder)
foldermake(down_folder)

##### Looping over tiles
for tile in subtiles:  # tiles.index:

    ### Tile skipper statement
    # if tile in skiptiles:
    #    print('Skipping tile ' + str(tile))
    #    continue

    ### Create tile folder structure
    tile_name = "tile_" + str(tile)

    print(
        "########### Processing tile "
        + str(tile)
        + "("
        + str(tilecount)
        + "/"
        + str(tiletot)
        + ")"
    )

    ######################### DOWNLOAD USING ARIA2 FOR SPEED AND WGET TO FIX ERRORS ################################

    print("########### Part 1 - Downloading images for tile " + str(tile))
    print("#### Querying ASF")

    ### Query data availability

    # Get bounding box for the selected tile as a comma separated string
    bbox = tiles.loc[tile, ["xmin", "ymin", "xmax", "ymax"]].apply(str).str.cat(sep=",")

    # Define ASF image query parameters
    params = (
        ("bbox", bbox),
        ("platform", "ALOS"),
        ("processingLevel", "L1.5"),
        ("beamMode", "FBD,FBS"),
        ("flightDirection", "ASC"),
        ("output", "csv"),
    )

    # Query the ASF API for PALSAR1 availability for the selected tile, using the parameters above
    req = requests.get(
        "https://api.daac.asf.alaska.edu/services/search/param", params=params
    )

    # Extract response from resulting query as data frame, keeping only URL, beam mode and file size
    imgquery = pd.read_csv(io.StringIO(req.content.decode("utf-8")))[
        ["URL", "Beam Mode", "Size (MB)"]
    ]

    ### Compute and display query summary

    # Per Beam Mode
    beamsummary = (
        imgquery.groupby("Beam Mode")
        .agg({"Beam Mode": "count", "Size (MB)": "sum"})
        .rename(columns={"Beam Mode": "Number of Images"})
    )
    print(beamsummary)

    # Total summary
    totsummary = imgquery.agg({"Beam Mode": "count", "Size (MB)": "sum"}).rename(
        columns={"Beam Mode": "Number of Images"}
    )

    # Save image list to csv, putting the number of images on the file name for easy checking
    csvname = (
        down_folder
        + "tile_"
        + str(tile)
        + "_"
        + str(beamsummary.iat[0, 0])
        + "_FBD_"
        + str(beamsummary.iat[1, 0])
        + "_FBS_"
        + str(len(imgquery))
        + "_available_imgs.csv"
    )

    imgquery.to_csv(csvname, encoding="utf-8")

    ### Downloading!

    print(
        "#### Starting download of tile "
        + str(tile)
        + ", with "
        + str(int(totsummary[0]))
        + " images, totaling "
        + str(round(totsummary[1], 2))
        + " Mb"
    )

    imglist = imgquery.URL.tolist()

    os.chdir(down_folder)
    ct = 1
    for img in imglist:
        print(
            "Downloading image "
            + str(ct)
            + " of "
            + str(int(totsummary[0]))
            + " for tile "
            + str(tile)
        )
        os.system(
            "wget --http-user=tsfsilva --http-password='Silva(1979)' -qq --show-progress --no-clobber --retry-connrefused --waitretry=1 -t 0 "
            + img
        )
        ct = ct + 1

    # Get url for download metalink for aria2
    # it's the same url as the csv request, just with a different 'output' parameter
    # print('Downloading files using Aria2 and metalink')
    # down_url = req.url[:-3] + 'metalink'
    # os.chdir(down_folder)
    # os.system('aria2c --http-auth-challenge=true --http-user=tsfsilva --http-passwd="Silva(1979)" -V -x 16 -s 16 -j 16 --summary-interval=0 --disable-ipv6=true "' + down_url + '"')
    # raise SystemExit('All good up to here')

    # print('Checking if there were unfinished downloads and finishing using wget (slooow :-[ )')

    # unf_aria = glob.glob(down_folder + '*.aria2')
    # outname = down_folder + img[40:]
    # os.system("wget --http-user=tsfsilva --http-password='Silva(1979)' -c -q --show-progress --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 0 " + img + ' -O ' + outname)

    tilecount += 1

    print("########### Finished downloading tile " + str(tile))
    print("###########################################")

