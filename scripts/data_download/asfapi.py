# Downloads PALSAR images from ASF using the API

### Import modules
import pandas as pd  # for manipulating tile and image information
import geopandas  # for reading tile index shapefile
import os  # for folder creation and sending commands to terminal
import requests  # for sending queries to ASF API
import io  # for decoding image list requested from ASF
import subprocess

### Defining custom functions

# Fun to check if dir exists and create it if it doesn't
def folderMake(name):
    if not os.path.exists(name):
        os.makedirs(name)
        print("Creating folder " + name)
    else:
        print("Folder " + name + " already exists!")


# Fun to query tile shapefile and extract tile bounds
def getBounds(tile_num, shapefile, index="tile_num"):
    tile_ref = pd.DataFrame(
        geopandas.read_file(shapefile).set_index(index)
    )  # sets the field to be used as index (should be tile_num)
    tile_bbox = (
        tile_ref.loc[tile_num, ["xmin", "ymin", "xmax", "ymax"]]
        .apply(str)
        .str.cat(sep=",")
    )  # extract bbox
    return tile_bbox


def queryASF(
    tile_num,
    shapefile,
    platform="ALOS",
    proclevel="L1.5",
    beammode="FBD,FBS",
    flightdir="ASC",
    output="csv",
    returncsv=False,
):
    # Define ASF image query parameters
    tile_bbox = getBounds(tile_num, shapefile)

    params = (
        ("bbox", tile_bbox),
        ("platform", platform),
        ("processingLevel", proclevel),
        ("beamMode", beammode),
        ("flightDirection", flightdir),
        ("output", output),
    )

    # Submit request to ASF server
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
        {"Beam Mode": "Total images"}
    )
    print(totsummary)

    # Save image list to csv, putting the number of images on the file name for easy checking
    if returncsv:
        return req, imgquery.to_csv
    else:
        return req


# Function do download using aria2
def getImages(req, down_folder):
    down_url = req.url[:-3] + "metalink"
    folderMake(down_folder)
    print(f"\nSaving files to {down_folder}")
    print("Downloading using Aria2")
    command = [
        "aria2c",
        "--http-auth-challenge=true",
        "--http-user=tsfsilva",
        '--http-passwd="Silva(1979)"',
        "-V",
        "-x 16",
        "-s 16",
        "-j 16",
        "--summary-interval=0",
        "--disable-ipv6=true",
        f"-d {down_folder}",
        down_url,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
