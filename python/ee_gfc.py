#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=3
# license         :GPLv3
# ==============================================================================

# Imports
import ee
import time
import os

# Initialize
ee.Initialize()


# ee_gfc.run_task
def run_task(perc, iso3, extent_latlong, scale=30, proj=None,
             folder=None):
    """Compute forest-cover change with Google EarthEngine.

    Compute the forest-cover change from Global Forest Change data
    with Python and GEE API. Export the results to Google Cloud
    Storage.

    Notes for GOOGLE EARTH ENGINE (abbreviated GEE):
    - GEE account is needed: https://earthengine.google.com.
    - GEE API Python client is needed: \
    https://developers.google.com/earth-engine/python_install.

    :param perc: Tree cover percentage threshold to define forest.
    :param iso3: Country ISO 3166-1 alpha-3 code.
    :param extent_latlong: List/tuple of region extent in lat/long
    (xmin, ymin, xmax, ymax).
    :param scale: Resolution in meters per pixel. Default to 30.
    :param proj: The projection for the export.
    :param folder: Name of the Google Drive folder to export to.

    :return: The Google EarthEngine task.

    """

    # Region
    region = ee.Geometry.Rectangle(extent_latlong, proj="EPSG:4326",
                                   geodesic=False)
    region = region.buffer(10000).bounds()
    export_coord = region.getInfo()["coordinates"]

    # Hansen map
    gfc = ee.Image('UMD/hansen/global_forest_change_2018_v1_6').clip(region)

    # Tree cover, loss, and gain
    treecover = gfc.select(["treecover2000"])
    lossyear = gfc.select(["lossyear"])

    # Forest in 2000
    forest2000 = treecover.gte(perc)

    # Deforestation
    loss00_10 = lossyear.gte(1).And(lossyear.lte(10))

    # Forest
    forest2010 = forest2000.where(loss00_10.eq(1), 0)
    forest2018 = forest2000.where(lossyear.gte(1), 0)

    # Forest raster with three bands
    forest = forest2000.addBands(forest2010).addBands(forest2018)
    forest = forest.select([0, 1, 2], ["forest2000", "forest2010",
                                       "forest2018"])
    forest = forest.set("system:bandNames", ["forest2000", 
                                             "forest2010",
                                             "forest2018"])

    # maxPixels
    maxPix = 1e13

    # Export forest to Google Drive
    # ! region must be lat/long coordinates with Python API.
    task = ee.batch.Export.image.toDrive(
        image=forest,
        description="forest_" + iso3,
        folder=folder,
        fileNamePrefix="forest_" + iso3,
        region=export_coord,
        scale=scale,
        maxPixels=maxPix,
        crs=proj)
    task.start()

    # Return task
    return(task)


# ee_jrc.check
def check(gs_bucket, iso3):
    """Function to check if the forest cover data are already present in
    the Google Cloud Storage (GCS) bucket.

    :param gs_bucket: the GCS bucket to look in.
    :param iso3: Country ISO 3166-1 alpha-3 code.

    :return: A boolean indicating the presence (True) of the data in
    the bucket.

    """

    # Connect to GCS bucket
    client = storage.Client()
    bucket = client.get_bucket(gs_bucket)
    # Filename to find
    fname = "global_forest_change/forest_" + iso3
    # Get a list of the blobs
    iterator = bucket.list_blobs()
    blobs = list(iterator)
    # Loop on blobs
    present_in_bucket = False
    for b in blobs:
        if b.name.find(fname) == 0:
            present_in_bucket = True
            break
    # Return
    return(present_in_bucket)


# ee_hansen.download
def download(gs_bucket, iso3, path):
    """Download forest-cover data from Google Cloud Storage.

    Check that GEE tasks are completed. Download forest-cover data
    from Google Cloud Storage in the current working directory. This
    function uses the gsutil command
    (https://cloud.google.com/storage/docs/gsutil)

    :param gs_bucket: Name of the google storage bucket to download from.
    :param iso3: Country ISO 3166-1 alpha-3 code.
    :param path: Path to download files to.

    """

    # Data availability
    data_availability = check(gs_bucket, iso3)

    # Check task status
    while data_availability is False:
            # We wait 1 min
            time.sleep(60)
            # We reactualize the status
            data_availability = check(gs_bucket, iso3)

    # Commands to download results with gsutil
    cmd = ["gsutil cp gs://", gs_bucket,
           "/global_forest_change/forest_", iso3, "*.tif ", path]
    cmd = "".join(cmd)
    os.system(cmd)

# End
