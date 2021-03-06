#!/usr/bin/python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# license         :GPLv3
# ==============================================================================

# PRIOR TO EXECUTING THE FOLLOWING SCRIPT, YOU MUST HAVE CREDENTIALS FOR
# 1. Google Earth Engine
# 2. rclone with Google Drive: https://rclone.org/drive/
# 3. WDPA: https://www.protectedplanet.net/

import sys
import os
import shutil  # for rmtree
import re  # regular expressions
import pkg_resources
import pandas as pd
import forestatrisk as far

os.chdir("/home/ghislain/Code/forestatrisk-newcaledonia")
from run_modelling_steps import run_modelling_steps

#index_ctry = int(sys.argv[1])-1

# ==================
# Settings
# Earth engine
import ee
ee.Initialize()
# WDPA API
from dotenv import load_dotenv
load_dotenv("/home/ghislain/Code/forestatrisk-tropics/.env")
from pywdpa import get_token
get_token()
# GDAL
os.environ["GDAL_CACHEMAX"] = "1024"
# PROJ
os.environ["PROJ_LIB"] = "/home/ghislain/.pyenv/versions/miniconda3-latest/envs/conda-far/share/proj"
# ==================

# Country isocode
file_ctry_run = pkg_resources.resource_filename("forestatrisk",
                                                "data/ctry_run.csv")
data_ctry_run = pd.read_csv(file_ctry_run, sep=";", header=0)
iso3 = list(data_ctry_run.iso3)
nctry = len(iso3)  # 120


# Function for multiprocessing
def run_country(iso3):

    # # GDAL temp directory
    # far.make_dir("/share/nas2-amap/gvieilledent/tmp/tmp_" + iso3)
    # os.environ["CPL_TMPDIR"] = "/share/nas2-amap/gvieilledent/tmp/tmp_" + iso3

    # Set original working directory
    cont = data_ctry_run.cont_run[data_ctry_run["iso3"] == iso3].iloc[0]
    owd = "/home/ghislain/Code/forestatrisk-newcaledonia/" + cont
    os.chdir(owd)
    far.make_dir(iso3)
    os.chdir(os.path.join(owd, iso3))

    # # Download data
    # far.data.country_forest_download(
    #     iso3,
    #     gdrive_remote_rclone="gdrive_gv",
    #     gdrive_folder="GEE-forestatrisk-NCL",
    #     output_dir="data_raw")

    # # Compute variables
    # far.data.country_compute(
    #     iso3,
    #     temp_dir="data_raw",
    #     output_dir="data",
    #     proj="EPSG:3395",
    #     data_country=False,
    #     data_forest=True,
    #     keep_temp_dir=True)

    # If not Brazil
    p = re.compile("BRA-.*")
    m = p.match(iso3)
    if m is None:
        # Model and Forecast
        run_modelling_steps(iso3, fcc_source="jrc")

    # # Remove GDAL temp directory
    # shutil.rmtree("/share/nas2-amap/gvieilledent/tmp/tmp_" + iso3)

    # Return country iso code
    return iso3

# Run country
run_country(iso3[85])

# ========================================================
# Additional figures
# ========================================================

import matplotlib.pyplot as plt

os.chdir("/home/ghislain/Code/forestatrisk-newcaledonia")
far.make_dir("figures")

# fcc123 with zoom
fig_fcc = far.plot.fcc123("Asia/NCL/data/forest/fcc123.tif",
                          maxpixels=1e8,
                          zoom=(18530000, 18600000, -2555000, -2500000),
                          borders="Asia/NCL/data/ctry_PROJ.shp",
                          output_file="figures/fcc123.png",
                          linewidth=0.5)
plt.close(fig_fcc)

# Original spatial random effects
fig_rho_orig = far.plot.rho("Asia/NCL/output/rho_orig.tif",
                            borders="Asia/NCL/data/ctry_PROJ.shp",
                            output_file="figures/rho_orig.png")
plt.close(fig_rho_orig)

# Spatial probability of deforestation
fig_prob = far.plot.prob("Asia/NCL/output/prob.tif",
                         maxpixels=1e8,
                         legend=True,
                         borders="Asia/NCL/data/ctry_PROJ.shp",
                         output_file="figures/prob.png",
                         linewidth=0.5)
plt.close(fig_prob)

# fcc_2100
fig_fcc = far.plot.fcc("Asia/NCL/output/fcc_2100.tif",
                       maxpixels=1e8,
                       borders="Asia/NCL/data/ctry_PROJ.shp",
                       output_file="figures/fcc_2100.png",
                       linewidth=0.5)
plt.close(fig_fcc)


# End
