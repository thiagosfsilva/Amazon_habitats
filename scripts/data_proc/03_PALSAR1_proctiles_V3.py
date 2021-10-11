# Downloads PALSAR images from ASF using the API

## For RStudio REPL
# library(reticulate)
# use_condaenv("osgeo")
# repl_python()

### Import modules
import os # for folder creation and sending commands to terminal
import shutil # for deleting files at the end
import sys # for supressing rsgislib printing
import glob # for general file listing
from os import path # for path manipulation
import rsgislib # for aligning images and renaming bands
from rsgislib import imageutils # idem above
import re # for regular expreession operations on strings
import numpy as np # for image calculations
from numpy import inf # idem above
import numpy.ma as ma # for dealing with missing data (NaN)
import scipy # for calculating skewness
from scipy import stats # idem above
import rasterio # for reading images as np arrays and saving back to image
import pandas as pd

###############################################
######## SET NECESSARY PATHS HERE  ############
###############################################

### Base directory for tile folders
basedir = '/mnt/Dados5/PEER_mapping/rasters/Amazon_tiles/tiles/'

down_folder = '/mnt/Dados5/PEER_mapping/rasters/Amazon_tiles/downloads/'

### Path to folder with reference raster grids for each tile
tile_grid_folder = '/mnt/Dados5/PEER_mapping/rasters/PEER_focus_grid_baseraster/'

##############################################
##############################################

### Defining custom functions

# Fun to check if dir exists and create it if not
def foldermake(name):
    if not os.path.exists(name):
        os.makedirs(name)
        print('Creating folder ' + name)
    else:
        print('Folder ' + name + ' already exists!')

############## PROCESSING STEPS START HERE ################''

# Make a global previews folder in the global folders
glob_prev = '/mnt/Dados5/PEER_mapping/rasters/PEER_tiles/previews/'
if not os.path.exists(glob_prev):
    os.makedirs(glob_prev)

############## PROCESSING STEPS START HERE ################
# Read tile image lists
tile_lists_full = sorted(glob.glob(down_folder + '*imgs.csv' )) #  [734:]
tile_subset = ["tile_1895"]
tile_lists = []
for x in tile_subset:
    tile_lists.extend([i for i in tile_lists_full if x in i])

tile_length = len(tile_lists)
counter = 1
#tile_lists = tile_lists[-10:]
#tile = tile_lists[1]

#tile

##### Looping over tiles
for tile in tile_lists:

    ### Get tile name and number
    tile_name = re.search("tile_[0-9]*",os.path.basename(tile)).group()
    tile_num =  int("".join(filter(str.isdigit, tile_name)))

    ### Get image List
    img_table = pd.read_csv(tile)
    img_list = [down_folder + os.path.basename(s) for s in img_table['URL']]

    ### Create tile folder structure
    tile_counter = " (" + str(counter) + '/' + str(tile_length) + ')'
    print('########### Processing tile ' + str(tile_num) + tile_counter)

    print('#### Setting directory tree')

    # Create main tile folder
    tile_folder = basedir + tile_name + '/'
    foldermake(tile_folder)

    # Create sensor folder
    sens_folder = tile_folder + 'PALSAR1/'
    foldermake(sens_folder)

    # create aligned images subfolder
    align_folder = sens_folder + 'aligned/'
    foldermake(align_folder)

    # Create extracted subfolder
    ext_folder = sens_folder + 'extracted/'
    foldermake(ext_folder)

    # Create folder for virtual stacks
    vrt_folder = sens_folder + 'VRTstacks/'
    foldermake(vrt_folder)

    # Create output composite path
    comp_folder = sens_folder + 'composites/'
    foldermake(comp_folder)

    # Create output preview path
    jpg_folder = sens_folder + 'preview/'
    foldermake(jpg_folder)

    ######################## EXTRACT IMAGES ################################

    print('#### Extracting images for tile ' + str(tile_num) + tile_counter)

    for img in img_list:
        os.system('unzip  -q -u ' + img + ' -d ' + ext_folder)

    # Remove zipfiles
    #print('#### Unzipping complete, removing zipfiles to save space')
    #os.system('rm ' + zip_path)

    print('### Finisehd Extracting')

    ######################## ALIGN IMAGES ################################

    print('### Aligning images for tile ' + str(tile_num) + tile_counter)

    # Get reference grid for this path
    tileref = tile_grid_folder + tile_name + '.tif'
    tileref
    ## Get image list from the extracted subfolder
    imglist = glob.glob(ext_folder + '**/IMG-H*.5_UA')
    imglist
    # proj4string to warp to
    proj4 = '"+proj=aea +lat_1=-5 +lat_2=-42 +lat_0=-32 +lon_0=-60 +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs"'

    print('#### Warping images as Virtual Rasters')
    ## Warp input images as VRTs, using the tile reference grid as base
    for inImg in imglist:
        inImgVRT = inImg[:-8] + '.vrt'
        print(inImgVRT)
        os.system('gdalwarp -q -t_srs ' + proj4 + ' -of VRT -overwrite ' + inImg + ' ' + inImgVRT)
        outImg = align_folder + os.path.basename(inImg)[:-8] + '_aligned.tif'
        #sys.stdout = open(os.devnull, "w")
        rsgislib.imageutils.resampleImage2Match(tileref, inImgVRT, outImg, 'GTiff', 'cubic')
        #sys.stdout = sys.__stdout__

    print('#### Renaming all files to include acquisition date')
    imgdirs = glob.glob(ext_folder + '**/')
    imgdirs
    # Build empty data frame to store filenames and dates
    imgdate_pd = pd.DataFrame(columns = ['file','date'])
    imgdate_pd
    # we need to loop over HH and HV files
    pols = ['HH','HV']

    # Looping over polarizations
    for pol in pols:
        #Looping over each folder
        for imgdir in imgdirs:
            try: # FBS images dont have HV bands, so they will throw and error
                imgfile = os.path.basename(glob.glob(imgdir + 'IMG-'+pol+'*.5_UA')[0])
            except: # if there is no HV and the error is raised, we skip to next iteration of the loop
                continue
            else: # if no error is raised, we go on
                metafile = str(glob.glob(imgdir + '/*.txt'))[2:-2] #get metadata filename
                with open(str(metafile), 'r') as in_file: #open metadata file and read into variable
                    metadata = in_file.read()
                imagedate = int(re.search('TIME(\t\d+)', metadata).group(1)[0:9]) # search the TIME tag for image datetime usinf regex, get date only
                file_date = {'file':imgfile[:-8],'date':imagedate} # create dict with filename and date to be appended to df
                imgdate_pd = imgdate_pd.append(file_date,ignore_index=True) # append filename and date to df

    # Get list of aligned images to be renamed
    alignfiles = glob.glob(align_folder + '*_aligned.tif')
    alignfiles
    # rename files using list of names and dates
    for item in alignfiles:
        shortname = os.path.basename(item)[:-12]
        date = str(int(imgdate_pd[imgdate_pd.file == shortname].date))
        newname = item[:-11] + date + item[-12:]
        os.rename(item,newname)

    # Save imgname and dates to csv
    csvname = align_folder + tile_name + '_aligned_img_dates.csv'
    imgdate_pd.to_csv(csvname,encoding='utf-8')

    ######################### MAKE COMPOSITES  ################################

    print('#### Making image composites for tile ' + str(tile_num) + tile_counter)

    # Calculate composites

    # List all HH and HV files in the aligned folder
    files_hh = glob.glob(align_folder + '/IMG-HH*.tif')
    files_hv = glob.glob(align_folder + '/IMG-HV*.tif')

    # Create virtual rasters to use as stacks
    # We create the file names separately so we can reuse them later
    vrt_hh = vrt_folder + 'AP1_' + tile_name + '_stack_HH.vrt'
    vrt_hv = vrt_folder + 'AP1_' + tile_name + '_stack_HV.vrt'

    # Pass gdal command to the system
    os.system('gdalbuildvrt -q -overwrite  -separate ' + vrt_hh + ' ' + ' '.join(files_hh))
    os.system('gdalbuildvrt -q -overwrite  -separate ' + vrt_hv + ' ' + ' '.join(files_hv))

    # Define output band names
    outMeanHH = comp_folder + 'AP1_' + tile_name + '_hh_mean.tif'
    outMedianHH = comp_folder + 'AP1_' + tile_name + '_hh_median.tif'
    outStdHH = comp_folder + 'AP1_' + tile_name +'_hh_std.tif'
    outCvHH = comp_folder + 'AP1_' + tile_name +'_hh_cv.tif'
    outMinHH = comp_folder + 'AP1_' + tile_name +'_hh_min.tif'
    outMaxHH = comp_folder + 'AP1_' + tile_name +'_hh_max.tif'
    outSkewHH = comp_folder + 'AP1_' + tile_name +'_hh_skewness.tif'
    outRangHH = comp_folder + 'AP1_' + tile_name +'_hh_range.tif'

    outMeanHV = comp_folder + 'AP1_' + tile_name + '_hv_mean.tif'
    outMedianHV = comp_folder + 'AP1_' + tile_name + '_hv_median.tif'
    outStdHV = comp_folder + 'AP1_' + tile_name +'_hv_std.tif'
    outCvHV = comp_folder + 'AP1_' + tile_name +'_hv_cv.tif'
    outMinHV = comp_folder + 'AP1_' + tile_name +'_hv_min.tif'
    outMaxHV = comp_folder + 'AP1_' + tile_name +'_hv_max.tif'
    outSkewHV = comp_folder + 'AP1_' + tile_name +'_hv_skewness.tif'
    outRangHV = comp_folder + 'AP1_' + tile_name +'_hv_range.tif'

    outHHHV = comp_folder + '/AP1_' + tile_name + '_hhhv.tif'

    # There will be some weird calculations because of nodata and small pixvalues
    np.seterr(divide='ignore',invalid='ignore')

    # Now open the HH VRTs using rasterio
    dataset_hh = rasterio.open(vrt_hh)
    hh_profile = dataset_hh.profile
    hh = dataset_hh.read().astype('float32')
    #hh.dtype
    hh[hh == 0] = 'nan'
    ##hh_mask = ma.masked_where(hh <= 0, hh)


    # Calculate temporal statistics for HH
    print('Calculating HH mean')
    hh_mean = np.nanmean(hh,0,dtype='float32')
    rasterio.open(outMeanHH,'w',driver='GTiff',count=1,height=dataset_hh.height,width=dataset_hh.width,dtype='float32',crs=dataset_hh.crs,transform=dataset_hh.transform).write(hh_mean,1)

    print('Calculating HH median')
    hh_median = np.nanmedian(hh,0)
    hh_median = np.float32(hh_median)
    rasterio.open(outMedianHH,'w',driver='GTiff',count=1,height=dataset_hh.height,width=dataset_hh.width,dtype='float32',crs=dataset_hh.crs,transform=dataset_hh.transform).write(hh_median,1)
    del hh_median

    print('Calculating HH standard deviation')
    hh_std = np.nanstd(hh,0,dtype='float32')
    rasterio.open(outStdHH,'w',driver='GTiff',count=1,height=dataset_hh.height,width=dataset_hh.width,dtype='float32',crs=dataset_hh.crs,transform=dataset_hh.transform).write(hh_std,1)

    print('Calculating HH coefficient of variation')
    hh_cv = np.divide(hh_std,hh_mean,dtype='float32')
    hh_cv[hh_cv == -inf] = 0
    hh_cv[hh_cv == inf] = 0
    hh_cv = np.nan_to_num(hh_cv)
    hh_cv = hh_cv
    rasterio.open(outCvHH,'w',driver='GTiff',count=1,height=dataset_hh.height,width=dataset_hh.width,dtype='float32',crs=dataset_hh.crs,transform=dataset_hh.transform).write(hh_cv,1)
    del hh_cv, hh_std

    print('Calculating HH min, max and range')
    hh_min = np.nanmin(hh,0)
    hh_max = np.nanmax(hh,0)
    hh_range = np.subtract(hh_max,hh_min,dtype='float32')
    rasterio.open(outMinHH,'w',driver='GTiff',count=1,height=dataset_hh.height,width=dataset_hh.width,dtype='float32',crs=dataset_hh.crs,transform=dataset_hh.transform).write(hh_min,1)
    rasterio.open(outMaxHH,'w',driver='GTiff',count=1,height=dataset_hh.height,width=dataset_hh.width,dtype='float32',crs=dataset_hh.crs,transform=dataset_hh.transform).write(hh_max,1)
    rasterio.open(outRangHH,'w',driver='GTiff',count=1,height=dataset_hh.height,width=dataset_hh.width,dtype='float32',crs=dataset_hh.crs,transform=dataset_hh.transform).write(hh_range,1)
    del hh_max,hh_min,hh_range

    print('Calculating HH skewness')
    hh_skew = scipy.stats.skew(hh,0,nan_policy='omit')
    hh_skew = np.float32(hh_skew)
    rasterio.open(outSkewHH,'w',driver='GTiff',count=1,height=dataset_hh.height,width=dataset_hh.width,dtype='float32',crs=dataset_hh.crs,transform=dataset_hh.transform).write(hh_skew,1)

    del hh
    dataset_hh.close()

    #### HV

    dataset_hv = rasterio.open(vrt_hv)
    hv_profile = dataset_hv.profile
    hv = dataset_hv.read().astype('float32')
    #hv.dtype
    hv[hv == 0] = 'nan'

    print('Calculating HV mean')
    hv_mean = np.nanmean(hv,0,dtype='float32')
    rasterio.open(outMeanHV,'w',driver='GTiff',count=1,height=dataset_hv.height,width=dataset_hv.width,dtype='float32',crs=dataset_hv.crs,transform=dataset_hv.transform).write(hv_mean,1)

    print('Calculating HV median')
    hv_median = np.nanmedian(hv,0)
    hv_median = np.float32(hv_median)
    rasterio.open(outMedianHV,'w',driver='GTiff',count=1,height=dataset_hh.height,width=dataset_hh.width,dtype='float32',crs=dataset_hh.crs,transform=dataset_hh.transform).write(hv_median,1)
    del hv_median

    print('Calculating HV standard deviation')
    hv_std = np.nanstd(hv,0,dtype='float32')
    rasterio.open(outStdHV,'w',driver='GTiff',count=1,height=dataset_hv.height,width=dataset_hv.width,dtype='float32',crs=dataset_hv.crs,transform=dataset_hv.transform).write(hv_std,1)

    print('Calculating HV coefficient of variation')
    hv_cv = np.divide(hv_std,hv_mean,dtype='float32')
    hv_cv[hv_cv == -inf] = 0
    hv_cv[hv_cv == inf] = 0
    hv_cv = np.nan_to_num(hv_cv)
    hv_cv = hv_cv
    rasterio.open(outCvHV,'w',driver='GTiff',count=1,height=dataset_hv.height,width=dataset_hv.width,dtype='float32',crs=dataset_hv.crs,transform=dataset_hv.transform).write(hv_cv,1)
    del hv_cv, hv_std

    print('Calculating HV min, max and range')
    hv_min = np.nanmin(hv,0)
    hv_max = np.nanmax(hv,0)
    hv_range = np.subtract(hv_max,hv_min,dtype='float32')
    rasterio.open(outMinHV,'w',driver='GTiff',count=1,height=dataset_hv.height,width=dataset_hv.width,dtype='float32',crs=dataset_hv.crs,transform=dataset_hv.transform).write(hv_min,1)
    rasterio.open(outMaxHV,'w',driver='GTiff',count=1,height=dataset_hv.height,width=dataset_hv.width,dtype='float32',crs=dataset_hv.crs,transform=dataset_hv.transform).write(hv_max,1)
    rasterio.open(outRangHV,'w',driver='GTiff',count=1,height=dataset_hv.height,width=dataset_hv.width,dtype='float32',crs=dataset_hv.crs,transform=dataset_hv.transform).write(hv_range,1)
    del hv_min,hv_max,hv_range

    print('Calculating HV skewness')
    hv_skew = scipy.stats.skew(hv,0,nan_policy='omit')
    hv_skew = np.float32(hv_skew)
    rasterio.open(outSkewHV,'w',driver='GTiff',count=1,height=dataset_hv.height,width=dataset_hv.width,dtype='float32',crs=dataset_hv.crs,transform=dataset_hv.transform).write(hv_skew,1)

    print('Calculating HH/HV ratio using means')
    hhhv = np.divide(hh_mean,hv_mean,dtype='float32')
    hhhv[hhhv == -inf] = 0
    hhhv[hhhv == inf] = 0
    hhhv = np.nan_to_num(hhhv)
    rasterio.open(outHHHV,'w',driver='GTiff',count=1,height=dataset_hh.height,width=dataset_hh.width,dtype='float32',crs=dataset_hh.crs,transform=dataset_hh.transform).write(hhhv,1)

    print('#### Making VRT composite stack and previews')

    # Get a list of all composite bands and make a sorted VRT stack
    comp_list = glob.glob(comp_folder + '/*.tif')
    comp_list = sorted(comp_list)

    comp_vrt = comp_folder + 'AP1_' + tile_name + '_HH_HV_composites.vrt'
    os.system('gdalbuildvrt -overwrite  -separate ' + comp_vrt + ' ' + ' '.join(comp_list))

    # Create list of band names using regex and rename the VRT bands
    name_list = [re.findall(r'(AP1?.*)(?=\.)',i)[0] for i in comp_list]
    imageutils.setBandNames(comp_vrt, name_list)

    ### Create RGB JPEG preview
    jpg_name = jpg_folder + os.path.basename(comp_vrt)[:-4] + '_preview.jpg'
    jpg_name2 = glob_prev + os.path.basename(comp_vrt)[:-4] + '_preview.jpg'
    os.system('gdal_translate -q -b 3 -b 12 -b 9 -of JPEG -ot Byte -scale_1 3700 7300 0 255 -scale_2 2100 4200 0 255 -scale_3 1.4 2 0 255 -outsize 20\% 20\% ' + comp_vrt + ' ' + jpg_name)
    os.system('gdal_translate -q -b 3 -b 12 -b 9 -of JPEG -ot Byte -scale_1 3700 7300 0 255 -scale_2 2100 4200 0 255 -scale_3 1.4 2 0 255 -outsize 20\% 20\% ' + comp_vrt + ' ' + jpg_name2)

    ### Remove extracted images to save space
    print('### Cleaning up')
    shutil.rmtree(ext_folder,ignore_errors=True)
    shutil.rmtree(align_folder,ignore_errors=True)

    print('########### Finished processing tile ' + str(tile_num) + tile_counter)
    print('###########################################')
    counter = counter + 1
