This is a demo map showing Landsat images around Costa Rica, comprising of seven WRS-2 zones:
14-53, 14-54, 14-55, 15-52, 15-53, 15-54, 16-52, and 16-53.

There are two moving parts here and a bit of curation: The backend proxy, the browser-based map, and a curated set of nearly cloudless images around the coast.


The first is a proxy that converts the desired bands (approximately visibile light, RGB) into a Cloud-Optimized GeoTIFF (COG) which can be displayed in a browser or similar client efficiently.
Cloud-Optimized GeoTIFFs exist already for Landsat 8 in AWS Public Data (`landsat-pds`), but not for Landsat 5 and 7,
justifying the existence of this approach. Landsat 8 images could be displayed from AWS directly here, though we opt not to do so here to make the processing uniform.

The proxy server stores each requested (whitelisted) Landsat scene in a filesystem cache in perpetuity, making it much faster to retrieve images for a given date once they've been retrieved before. For optimal results, pre-fetch all images before use.


Second, we display the satellite images in a browser-based map (under `client-map`).
This is a fork of the excellent [https://geotiffjs.github.io/](GeoTIFF.js) demo application [COG explorer](https://geotiffjs.github.io/cog-explorer/).
The image display is tuned to improve the contrast somewhat, though the result is uneven across different instruments.


There is a third component, a classification index file (`coral_idx.json`), which further limits the images being shown from *all* Landsat images in the region, to a curated time series spanning around 600 images in total.

In this case, this data has been classified so as to only show those images which are almost cloudless
*around the coast*.
Because Landsat's FMask algorithm didn't yield sufficiently accurate results, this was done manually for the mere ~3000 images in this time period (Landsat 5-8, i.e. from 1984 onwards).


Known errors
===
1. Some of the images seem to have small patches of red/green/blue "noise". This might be a parsing bug in the GeoTIFF.js library.
2. The performance is not great. This is essentially a proof-of-concept to see if this warrants further investment.
3. Browser compatibility is not a goal for this POC application and Chrome in particular seems to get worse results here.
