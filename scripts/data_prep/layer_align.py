import rsgislib
from rsgislib import imageutils
import glob


mainPath = "/home/thiago/Projects/Amazon_habitats/data/test_data/"
tilePath = "tile_1743/"

refImg = mainPath + tilePath + "PALSAR1/AP1_tile_1743_hh_median.tif"
# maskImg = mainPath + tilePath + "tile_1743_cut.tif"
# demImg = mainPath + "AWD3D_amazon_mosaic.tif"

wetNDVI = "/home/thiago/Projects/Amazon_habitats/data/test_data/tile_1743/L5/MAM_Wet_season_NDVI.tif"
dryNDVI = "/home/thiago/Projects/Amazon_habitats/data/test_data/tile_1743/L5/MAM_Dry_season_NDVI.tif"
wetNDWI = "/home/thiago/Projects/Amazon_habitats/data/test_data/tile_1743/L5/MAM_Wet_season_NDWI.tif"
dryNDWI = "/home/thiago/Projects/Amazon_habitats/data/test_data/tile_1743/L5/MAM_Dry_season_NDWI.tif"

# rsgislib.imageutils.resampleImage2Match(
#     refImg,
#     maskImg,
#     mainPath + tilePath + "Class_mask_tile_1743.tif",
#     "GTiff",
#     "nearestneighbour",
#     9,
#     True,
# )
# rsgislib.imageutils.resampleImage2Match(
#     refImg,
#     demImg,
#     mainPath + tilePath + "DEM_median_tile_1743.tif",
#     "GTiff",
#     "cubic",
#     9,
#     True,
# )
rsgislib.imageutils.resampleImage2Match(
    refImg,
    wetNDVI,
    mainPath + tilePath + "wet_season_NDVI_tile_1743.tif",
    "GTiff",
    "cubic",
    9,
    True,
)
rsgislib.imageutils.resampleImage2Match(
    refImg,
    dryNDVI,
    mainPath + tilePath + "dry_season_NDVI_tile_1743.tif",
    "GTiff",
    "cubic",
    9,
    True,
)
rsgislib.imageutils.resampleImage2Match(
    refImg,
    wetNDWI,
    mainPath + tilePath + "wet_season_NDWI_tile_1743.tif",
    "GTiff",
    "cubic",
    9,
    True,
)
rsgislib.imageutils.resampleImage2Match(
    refImg,
    dryNDWI,
    mainPath + tilePath + "dry_season_NDWI_tile_1743.tif",
    "GTiff",
    "cubic",
    9,
    True,
)
