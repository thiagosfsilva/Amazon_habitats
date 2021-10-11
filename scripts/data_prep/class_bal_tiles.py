import glob
import pandas as pd
from PIL import Image
import numpy as np

tile_list = glob.glob("/media/thiago/Dados5/PEER_mapping/rasters/Hess_to_PEER/Hess_sample_tiles/tile_*.tif") 

tile_counts = pd.DataFrame(index = range(len(tile_list)), columns = ["tile",0,1,2,3,4,5,255])

i = 0

for tile in tile_list:
    image = Image.open(tile_list[554])
    arr = np.asarray(image)
    uniq, counts = np.unique(arr, return_counts=True)
    percs = np.rint(np.divide(counts,arr.shape[0]*arr.shape[1])*100)
    tile[i,"0"] = 
