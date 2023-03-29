# -*- coding: utf-8 -*-
"""Copy_of_exploratory_analisys.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1v2PuAsYzz_QlmG2W9AtwAkb93LHjugAP

# NCI GDC Dataset Analisys

### Download the dataset
"""
import time
from multiprocessing import Process
import openslide
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator
import numpy as np
from matplotlib import pyplot as plt
import os
import pandas as pd
import shutil

"""https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5226799/
http://wwwx.cs.unc.edu/~mn/sites/default/files/macenko2009.pdf

### List available images
"""


def norm_HnE(img, Io=240, alpha=1, beta=0.15):
    # Step 1: Convert RGB to OD ###################
    # reference H&E OD matrix.
    # Can be updated if you know the best values for your image.
    # Otherwise use the following default values.
    # Read the above referenced papers on this topic.
    HERef = np.array([[0.5626, 0.2159],
                      [0.7201, 0.8012],
                      [0.4062, 0.5581]])
    # reference maximum stain concentrations for H&E
    maxCRef = np.array([1.9705, 1.0308])

    # extract the height, width and num of channels of image
    h, w, c = img.shape

    # reshape image to multiple rows and 3 columns.
    # Num of rows depends on the image size (wxh)
    img = img.reshape((-1, 3))

    # calculate optical density
    # OD = −log10(I)
    # OD = -np.log10(img+0.004)  #Use this when reading images with skimage
    # Adding 0.004 just to avoid log of zero.

    OD = -np.log10((img.astype(float) + 1) / Io)  # Use this for opencv imread
    # Add 1 in case any pixels in the image have a value of 0 (log 0 is indeterminate)

    # Step 2: Remove data with OD intensity less than β ############
    # remove transparent pixels (clear region with no tissue)
    ODhat = OD[~np.any(OD < beta, axis=1)]  # Returns an array where OD values are above beta
    # Check by printing ODhat.min()

    # Step 3: Calculate SVD on the OD tuples ######################
    # Estimate covariance matrix of ODhat (transposed)
    # and then compute eigen values & eigenvectors.
    eigvals, eigvecs = np.linalg.eigh(np.cov(ODhat.T))

    # Step 4: Create plane from the SVD directions with two largest values ######
    # project on the plane spanned by the eigenvectors corresponding to the two
    # largest eigenvalues
    That = ODhat.dot(eigvecs[:, 1:3])  # Dot product

    # Step 5: Project data onto the plane, and normalize to unit length ###########
    # Step 6: Calculate angle of each point wrt the first SVD direction ########
    # find the min and max vectors and project back to OD space
    phi = np.arctan2(That[:, 1], That[:, 0])

    minPhi = np.percentile(phi, alpha)
    maxPhi = np.percentile(phi, 100 - alpha)

    vMin = eigvecs[:, 1:3].dot(np.array([(np.cos(minPhi), np.sin(minPhi))]).T)
    vMax = eigvecs[:, 1:3].dot(np.array([(np.cos(maxPhi), np.sin(maxPhi))]).T)

    # a heuristic to make the vector corresponding to hematoxylin first and the
    # one corresponding to eosin second
    if vMin[0] > vMax[0]:
        HE = np.array((vMin[:, 0], vMax[:, 0])).T

    else:
        HE = np.array((vMax[:, 0], vMin[:, 0])).T

    # rows correspond to channels (RGB), columns to OD values
    Y = np.reshape(OD, (-1, 3)).T

    # determine concentrations of the individual stains
    C = np.linalg.lstsq(HE, Y, rcond=None)[0]

    # normalize stain concentrations
    maxC = np.array([np.percentile(C[0, :], 99), np.percentile(C[1, :], 99)])
    tmp = np.divide(maxC, maxCRef)
    C2 = np.divide(C, tmp[:, np.newaxis])

    # Step 8: Convert extreme values back to OD space
    # recreate the normalized image using reference mixing matrix

    Inorm = np.multiply(Io, np.exp(-HERef.dot(C2)))
    Inorm[Inorm > 255] = 254
    Inorm = np.reshape(Inorm.T, (h, w, 3)).astype(np.uint8)

    # Separating H and E components

    H = np.multiply(Io, np.exp(np.expand_dims(-HERef[:, 0], axis=1).dot(np.expand_dims(C2[0, :], axis=0))))
    H[H > 255] = 254
    H = np.reshape(H.T, (h, w, 3)).astype(np.uint8)

    E = np.multiply(Io, np.exp(np.expand_dims(-HERef[:, 1], axis=1).dot(np.expand_dims(C2[1, :], axis=0))))
    E[E > 255] = 254
    E = np.reshape(E.T, (h, w, 3)).astype(np.uint8)

    return Inorm, H, E


def save_loop(row1, col1, directory):
    for row in row1:
        for col in col1:
            tile_name = os.path.join(directory, '%d_%d' % (col, row))
            # print("Now saving tile with title: ", tile_name)
            temp_tile = tiles.get_tile(17, (col, row))
            temp_tile_rgb = temp_tile.convert('RGB')
            temp_tile_np = np.array(temp_tile_rgb)
            if temp_tile_np.mean() < 150 and temp_tile_np.std() > 15:
                # print("****Good tile number:", tile_name)
                plt.imsave(tile_name + ".png", temp_tile_np)
                # norm_img, H_img, E_img = norm_HnE(temp_tile_np, Io=240, alpha=1, beta=0.15)
                #
                # #Save the norm tile, H and E tiles
                # plt.imsave(tile_name + "_norm.png", norm_img)
                # plt.imsave(tile_name + "_H.png", H_img)
                # plt.imsave(tile_name + "_E.png", E_img)


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


SLIDES_PATH = './slides'

manifest = pd.read_csv(
    SLIDES_PATH + '/gdc_manifest_20230223_173244.txt',
    delimiter='\t'
)
manifest.head()
start = time.perf_counter()

for k in range(len(manifest)):
    til_dir = f"{SLIDES_PATH}/{manifest.id[k]}/tiles"
    if os.path.exists(til_dir):
        shutil.rmtree(til_dir)
    os.makedirs(til_dir, exist_ok=True)
    tile_dir = f"{SLIDES_PATH}/{manifest.id[k]}/tiles"

    f"{SLIDES_PATH}/{manifest.id[k]}/{manifest.filename[k]}"

    # Load the slide file (svs) into an object.
    slide = open_slide(f"{SLIDES_PATH}/{manifest.id[k]}/{manifest.filename[k]}")

    slide_props = slide.properties
    # print(slide_props.values())
    # print("Vendor is:", slide_props['openslide.vendor'])
    # print("Pixel size of X in um is:", slide_props['openslide.mpp-x'])
    # print("Pixel size of Y in um is:", slide_props['openslide.mpp-y'])

    # Objective used to capture the image
    objective = float(slide.properties[openslide.PROPERTY_NAME_OBJECTIVE_POWER])
    # print("The objective power is: ", objective)

    # get slide dimensions for the level 0 - max resolution level
    slide_dims = slide.dimensions
    # print(slide_dims)

    # Get a thumbnail of the image and visualize
    slide_thumb_600 = slide.get_thumbnail(size=(600, 600))

    # Convert thumbnail to numpy array
    slide_thumb_600_np = np.array(slide_thumb_600)
    plt.figure(figsize=(8, 8))
    plt.imshow(slide_thumb_600_np)

    # Get slide dims at each level. Remember that whole slide images store information
    # as pyramid at various levels
    dims = slide.level_dimensions

    num_levels = len(dims)
    # print("Number of levels in this image are:", num_levels)

    # print("Dimensions of various levels in this image are:", dims)

    # By how much are levels downsampled from the original image?
    factors = slide.level_downsamples
    # print("Each level is downsampled by an amount of: ", factors)

    # Copy an image from a level
    level4_dim = dims[3]

    # Size of your output image
    # Remember that the output would be a RGBA image (Not, RGB)
    level4_img = slide.read_region((0, 0), 3, level4_dim)  # Pillow object, mode=RGBA

    # Convert the image to RGB
    level4_img_RGB = level4_img.convert('RGB')


    # Convert the image into numpy array for processing
    level4_img_np = np.array(level4_img_RGB)
    plt.imshow(level4_img_np)

    # Return the best level for displaying the given downsample.
    SCALE_FACTOR = 32
    best_level = slide.get_best_level_for_downsample(SCALE_FACTOR)
    # Here it returns the best level to be 2 (third level)
    # If you change the scale factor to 2, it will suggest the best level to be 0 (our 1st level)
    #################################

    # Generating tiles for deep learning training or other processing purposes
    # We can use read_region function and slide over the large image to extract tiles
    # but an easier approach would be to use DeepZoom based generator.
    # https://openslide.org/api/python/

    # Generate object for tiles using the DeepZoomGenerator
    tiles = DeepZoomGenerator(slide, tile_size=256, overlap=0, limit_bounds=False)
    # Here, we have divided our svs into tiles of size 256 with no overlap.
    # The tiles object also contains data at many levels.
    # To check the number of levels
    # print("The number of levels in the tiles object are: ", tiles.level_count)
    # print("The dimensions of data in each level are: ", tiles.level_dimensions)
    #
    # Total number of tiles in the tiles object
    # print("Total number of tiles = : ", tiles.tile_count)

    # How many tiles at a specific level?
    level_num = 17
    level_dim = tiles.level_tiles[level_num]
    # print("Tiles at level ", level_num, " is: ", level_dim)
    # print("This means there are ", level_dim[0]*level_dim[1], " total tiles in this level")

    # Dimensions of the tile (tile size) for a specific tile from a specific layer
    tile_dims = tiles.get_tile_dimensions(level_num, (0, 0))  # Provide deep zoom level and address (column, row)
    # print("Tile (0,0)'s shape at level ", level_num, " is: ", tile_dims)

    # Dimensions of the tile (tile size) for a specific tile from a specific layer
    tile_dims = tiles.get_tile_dimensions(level_num, (level_dim[0] - 1, level_dim[1] - 1))  # Provide deep zoom level and address (column, row)
    # print("Tile ", (level_dim[0]-1, level_dim[1]-1), "'s shape at level ", level_num, " is: ", tile_dims)

    single_tile = tiles.get_tile(17, (62, 70))  # Provide deep zoom level and address (column, row)
    single_tile_RGB = single_tile.convert('RGB')

    # Saving each tile to local directory
    cols, rows = tiles.level_tiles[17]

    n = len(os.sched_getaffinity(0))
    t_rows = tuple(split(range(rows), n))
    t_cols = tuple(split(range(cols), n))
    processes = []
    for i in range(n):
        for j in range(n):
            p = Process(target=save_loop, args=(t_rows[i], t_cols[j], tile_dir))
            p.start()
            processes.append(p)
    for p in processes:
        p.join()
    end = time.perf_counter()
    print(round(end - start))
print("Done")