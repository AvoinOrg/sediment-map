#!/usr/bin/env python3
'''
This is a proxy to get Landsat images from the Google Cloud Platform
as Cloud-Optimized GeoTIFF images.

The data file being used, gcp_landsat_index.csv, is a subset of the 


Dependencies:
conda install -c conda-forge rio-cogeo flask rasterio numpy waitress -y

Running:
GOOGLE_APPLICATION_CREDENTIALS=... waitress-serve --call 'landsat_cog_proxy:create_app'
'''

from collections import *
from pathlib import *
from rasterio.io import MemoryFile
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from threading import Lock
import contextlib
import csv
import flask
import glob, os, sys, re
import numpy as np
import rasterio

NODATA = 0
CHANNELS = 3

gcloud_scene_entries = {
    x['SCENE_ID'] : x
    for x in csv.DictReader(open('gcp_landsat_index.csv', 'rt'))
    if x['PRODUCT_ID']
}

BASE_URL = 'https://mapsearch.curiosity.consulting'

for x in gcloud_scene_entries: print(x)

locks = defaultdict(Lock)


def render_cog(sceneid):
    out_name = f"cog_{sceneid}_orig.tif"
    if os.path.exists(Path('data') / out_name): return out_name

    gcloud_entry = gcloud_scene_entries[sceneid]
    if not gcloud_entry: return None

    GS_PREFIX = gcloud_entry['BASE_URL']
    qa_url = GS_PREFIX + '/' + GS_PREFIX.split('/')[-1] + '_BQA.TIF'

    sensor    = sceneid[1]
    satellite = int( sceneid[2] )

    print(f'satellite:{satellite} sensor:{sensor} scene:{sceneid} sceneid:{sceneid}')
    if satellite==8:
        bands = 4,3,2
    if satellite == 5 and sensor == 'M':
        # Duplicate the green and blue bands since the wavelengths don't really cover distinct bands
        bands = 2,1,1
    else:
        bands = 3,2,1

    print(sceneid, bands)

    band_files = [GS_PREFIX + '/' + GS_PREFIX.split('/')[-1] + f'_B{band}.TIF' for band in bands]

    with contextlib.ExitStack() as stack:
        qa_reader = stack.enter_context(rasterio.open(qa_url))
        qa = qa_reader.read()

        # NB: inline documentation is WRONG. Website documentation is correct, however:
        # https://www.usgs.gov/land-resources/nli/landsat/landsat-collection-1-level-1-quality-assessment-band?qt-science_support_page_related_con=0#qt-science_support_page_related_con
        fill,dropped_pixel,radio_sat1,radio_sat2,cloud,cloud_confidence,cloud_confidence2,cloud_shadow_confidence,cloud_shadow_confidence2,snow_ice_confidence,snow_ice_confidence2 = [1<<n for n in range(11)]
        valid_mask = (qa & (fill | dropped_pixel)) == 0

        readers = [stack.enter_context(rasterio.open(path)) for path in band_files]
        src = readers[0]

        raster_bands = [r.read() for r in readers]

        source_raster = np.stack(raster_bands).squeeze(1)
        source_raster[:, ~valid_mask.squeeze(0)] = NODATA

        src_ch, src_height, src_width = source_raster.shape

        src_profile = src.meta.copy()
        src_profile.update(dict(
            driver="GTiff",
            dtype=src.profile['dtype'],
            count=CHANNELS,
            nodata=NODATA,
        ))

        dst_profile = cog_profiles.get("deflate")

        memfile_orig = stack.enter_context( MemoryFile() )
        mem_orig     = stack.enter_context( memfile_orig.open(**src_profile) )
        mem_orig.write(source_raster)

        cog_translate(
            mem_orig,
            f"{out_name}.tmp",
            dst_profile,
            in_memory=True,
            quiet=True,
            web_optimized=True,
        )
        os.rename(f"{out_name}.tmp", Path('data') / out_name)

        print('Wrote', out_name)

        return out_name




app = flask.Flask(__name__)

@app.route('/scenes/<sceneid>')
def hello_world(sceneid: str):
    if sceneid not in gcloud_scene_entries: return '', 404

    with locks[sceneid]:
        fname = render_cog(sceneid)

    if not fname: return '', 500

    # Redirect to the finished (cached) static file so that
    # efficient partial sendfile responses are possible.
    return flask.redirect(f"{BASE_URL}/data/{fname}", code=307)



def create_app(*args, **kwargs):
    return app
