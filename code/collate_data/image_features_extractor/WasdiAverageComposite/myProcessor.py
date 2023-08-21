import sys
import wasdi
# builtin modules
from os import path
import tempfile
import zipfile
# GIS modules pre-installed in wasdi
from osgeo import gdal
from osgeo import osr
import numpy as np
import geopy.distance
from datetime import datetime



def run():
    wasdi.wasdiLog('CityWatch preprocessing S2')
    bTestOutTiff = 0

    #td1 = time.time()

    try:
        # retrieve parameters
        # bbox
        oBbox = wasdi.getParameter('BBOX', None)
        # Spatial resolution
        iXr = wasdi.getParameter('SPATIAL_RESOLUTION_M', 10)
        # same on Y
        iYr = iXr
        # Data Provider
        sProvider = wasdi.getParameter('PROVIDER', 'LSA')
        # Delete Flag
        bDelete = wasdi.getParameter('DELETE', False)
        # Minimum percentage of coverage of the image w.r.t. the AOI
        iMinimumCoverage = wasdi.getParameter('minCoveragePerc', 50)

        # List with the names of the bands to be processed
        asBands = wasdi.getParameter('BAND_NAMES', None)
        # List with the names of the tiles to be processed
        asTiles = wasdi.getParameter('TILE_NAMES', None)
        # Initial date of the time range
        sStartDate = wasdi.getParameter('START_DATE', None)
        # End date of the time range
        sEndDate = wasdi.getParameter('END_DATE', None)

        # Compute in memory?
        bInMemory = wasdi.getParameter('WorkInMemory', False)

        # Base name of the output map: average (per band) of all S2 images in the time range, over the AOI
        sOutputBaseName = wasdi.getParameter('OUTPUT_BASENAME', "UrbanArea.tif")

        # Stop the run if the diagonal of the bbox is longer than
        iDiagonalKm = wasdi.getParameter('DIAGONAL_KM', 200)
        # Stop the run if number of days before START_DATE and END_DATE is more than
        iMaxDays = wasdi.getParameter('MAX_DAYS_START_END', 1000)
        # Stop the run if number of tiles is more than
        iMaxNumberOfTiles = wasdi.getParameter('MAX_N_TILES', 10)

    except Exception as oE:
        wasdi.wasdiLog(f'Error reading the parameters: {type(oE)}: {oE}')
        wasdi.updateStatus('ERROR', 0)
        sys.exit(oE)

    # Number of bands
    iNumberOfBands = len(asBands)


    # conditions to stop the computation
    wasdi.wasdiLog("Checking the size of the Bounding Box")
    oBboxNE = oBbox["northEast"]
    oBboxSW = oBbox["southWest"]
    fLonW = oBboxSW["lng"]
    fLatS = oBboxSW["lat"]
    fLonE = oBboxNE["lng"]
    fLatN = oBboxNE["lat"]

    # make sure the bBox is not too big
    aoCoords_1 = (fLatN, fLonE)
    aoCoords_2 = (fLatS, fLonW)
    fDistKilometers = geopy.distance.geodesic(aoCoords_1, aoCoords_2).km
    if fDistKilometers > iDiagonalKm:
        wasdi.wasdiLog("The Bounding Box is too large: try reducing its size")
        wasdi.updateStatus("ERROR")
        sys.exit(1)
    else:
        wasdi.wasdiLog("Size of the Bounding Box acceptable")

    wasdi.wasdiLog("Checking the number of days to look for S2 images")
    oStartDateS2 = datetime.strptime(sStartDate, '%Y-%m-%d')
    oEndDateS2 = datetime.strptime(sEndDate, '%Y-%m-%d')
    iDays = (oEndDateS2 - oStartDateS2).days
    if iDays > iMaxDays:
        wasdi.wasdiLog("Too many days to look for S2 images: try reducing its number")
        wasdi.updateStatus("ERROR")
        sys.exit(1)
    else:
        wasdi.wasdiLog("Number of days to look for S2 images acceptable")

    aoS2L2Images = searchImages(oBbox, sEndDate, sProvider, sStartDate)

    asTiles = getTiles(aoS2L2Images, asTiles)

    wasdi.wasdiLog("Checking the number of tiles to process")
    if len(asTiles) > iMaxNumberOfTiles:
        wasdi.wasdiLog("Too many tiles to process: try reducing its number")
        wasdi.updateStatus("ERROR")
        sys.exit(1)
    else:
        wasdi.wasdiLog("Number of tiles to process acceptable")

    # compute averages, tile by tile
    asProductsAvailableAllTiles = []
    try:
        asEPSG = []
        asAverageTiles = []
        iNumberProcessedTiles = 0
        # Loop through all the tiles
        for sTile in asTiles:
            sAverageTile = 'Average_' + sTile + '.tif'
            asProductsInWorkspace = wasdi.getProductsByActiveWorkspace()
            if sAverageTile not in asProductsInWorkspace:
                wasdi.wasdiLog('Processing now tile ' + sTile)

                # Identify images of that tile
                aoS2L2ImagesPerTile = []
                asProductsInWorkspace = wasdi.getProductsByActiveWorkspace()
                for oS2L2Image in aoS2L2Images:
                    sS2L2Name = oS2L2Image["title"] + ".zip"
                    if sTile in sS2L2Name and "N9999" not in sS2L2Name:
                        aoS2L2ImagesPerTile.append(oS2L2Image)

                wasdi.wasdiLog('Products found in wasdi: {}'.format(len(aoS2L2ImagesPerTile)))

                asImagesAlreadyDown = [aoIm['title'] for aoIm in aoS2L2ImagesPerTile if aoIm['title'] + '.zip' in asProductsInWorkspace]
                wasdi.wasdiLog('Products already in workspace: {}'.format(len(asImagesAlreadyDown)))
                aoImagesToDownload = [aoIm for aoIm in aoS2L2ImagesPerTile if aoIm['title'] + '.zip' not in asProductsInWorkspace]

                asImagesDownloaded = []
                if aoImagesToDownload:
                    wasdi.wasdiLog('Products to import: {}'.format(len(aoImagesToDownload)))
                    asImportResultStatuses = wasdi.importProductList(aoImagesToDownload)
                    asImagesDownloaded = [aoAoi['title'] for aoAoi, aoResult in zip(aoS2L2ImagesPerTile, asImportResultStatuses) if aoResult == 'DONE']
                    wasdi.wasdiLog('Products imported: {}'.format(len(asImagesDownloaded)))

                asProductsAvailable = asImagesAlreadyDown + asImagesDownloaded
                if len(asProductsAvailable) <= 0:
                    wasdi.wasdiLog('No products available for the query. Aborting (sorry)')
                    wasdi.updateStatus('DONE', 100)
                    sys.exit(0)

                asProductsAvailableAllTiles.append(asProductsAvailable)

                # Number of processed files
                iProcessedFiles = 0
                # Array with the output values
                afOutputs = None
                # Array with the count of images summed for each pixel
                afCounts = None

                # start loop per image (within that tile)...
                for sProduct in asProductsAvailable:
                    wasdi.wasdiLog('Processing product ' + sProduct)

                    asBandsZipped, sSCLZipped, sTmpDir, sWorkPath = collectBandsPaths(asBands, bInMemory, sProduct)

                    asBandsWarped, sSCLWarped = warp(asBandsZipped, iXr, iYr, sSCLZipped, sWorkPath)

                    # mask for clouds
                    # get SCL band
                    oSCL = gdal.Open(sSCLWarped)
                    iRows = oSCL.RasterYSize
                    iCols = oSCL.RasterXSize
                    oRasterSCL = oSCL.GetRasterBand(1)
                    aiSCLAsArray = oRasterSCL.ReadAsArray(0, 0, iCols, iRows)

                    proj = osr.SpatialReference(wkt=oSCL.GetProjection())
                    sEPSG = proj.GetAttrValue('AUTHORITY', 1)
                    asEPSG.append(sEPSG)
                    wasdi.wasdiLog('Collected EPSG from SCL')

                    oShape = aiSCLAsArray.shape
                    oShape3D = oShape + (iNumberOfBands,)
                    if oShape[0] * oShape[1] > 100527 * 115126:
                        wasdi.wasdiLog(
                            'trying to allocate a matrix which is rather large, this is likely to fail. Please consider using a smaller bounding box')
                    if oShape3D[0] * oShape3D[1] * oShape3D[2] > 100527 * 115126:
                        wasdi.wasdiLog(
                            'trying to allocate a matrix which is rather large, this is likely to fail. Please consider using a smaller bounding box')


                    #to test if it makes the average per band correctly
                    if bTestOutTiff == 1:
                        sNameTiff = sProduct + '_bands.tif'
                        oDriver = gdal.GetDriverByName("GTiff")
                        oOutTiff = oDriver.Create(wasdi.getPath(sNameTiff), iRows, iCols,
                                                    iNumberOfBands, gdal.GDT_Float32, ['COMPRESS=LZW', 'BIGTIFF=YES'])
                        # sets same geotransform as one of the bands
                        oOutTiff.SetGeoTransform(oSCL.GetGeoTransform())
                        # sets same projection as one of the bands
                        oOutTiff.SetProjection(oSCL.GetProjection())

                    afCounts, afOutputs, iCols, iRows = applySCL(afCounts, afOutputs, aiSCLAsArray, asBandsWarped,
                                                                 bTestOutTiff, iCols, iProcessedFiles, iRows, oOutTiff,
                                                                 oShape3D, sProduct)
                    # del oSCL
                    del oRasterSCL
                    del aiSCLAsArray


                    # saves to disk
                    if bTestOutTiff == 1:
                        oOutTiff.FlushCache()
                        wasdi.wasdiLog("Saved tiff " + sNameTiff)
                        wasdi.addFileToWASDI(sNameTiff)
                        wasdi.wasdiLog("Tiff added to workspace")

                oDriver = gdal.GetDriverByName("GTiff")
                oOutAverageTile = oDriver.Create(wasdi.getPath(sAverageTile), iRows, iCols,
                                                   iNumberOfBands, gdal.GDT_Float32, ['COMPRESS=LZW', 'BIGTIFF=YES'])
                # sets same geotransform as one of the bands
                oOutAverageTile.SetGeoTransform(oSCL.GetGeoTransform())
                # sets same projection as one of the bands
                oOutAverageTile.SetProjection(oSCL.GetProjection())
                del oSCL

                wasdi.wasdiLog('Computing average of all images in tile ' + sTile)

                afAverageBand = np.empty(oShape)  # preinit
                #afAverageBand[:] = -9999
                afAverageBand[:] = np.nan
                adNan = np.empty(oShape)  # preinit
                #adNan[:] = -9999
                adNan[:] = np.nan

                for iBand in range(iNumberOfBands):
                    # only divide when denumerator different from adNan
                    afAverageBand = np.divide(afOutputs[:,:,iBand], afCounts[:,:,iBand], out=adNan, where=afCounts[:,:,iBand] != 0)
                    # round
                    #oOutAverageTile.GetRasterBand(iBand+1).WriteArray( np.rint(afAverageBand) )
                    # write
                    oOutAverageTile.GetRasterBand(iBand+1).WriteArray(afAverageBand)
                    # Set a no data value if required
                    #oOutAverageTile.GetRasterBand(iBand+1).SetNoDataValue(-9999)
                    oOutAverageTile.GetRasterBand(iBand+1).SetNoDataValue(np.nan)

                # saves to disk
                oOutAverageTile.FlushCache()
                wasdi.wasdiLog("Saved " + sAverageTile + " for tile " + sTile)
                wasdi.addFileToWASDI(sAverageTile)
                wasdi.wasdiLog("Average for tile " + sTile + " added to workspace")

                asAverageTiles.append(sAverageTile)

            else:
                # we already have this tile
                wasdi.wasdiLog('Tile ' + sTile + ' already in workspace')
                asAverageTiles.append(sAverageTile)

                oAverageTile = gdal.Open(wasdi.getPath(sAverageTile))

                proj = osr.SpatialReference(wkt=oAverageTile.GetProjection())
                sEPSG = proj.GetAttrValue('AUTHORITY', 1)
                asEPSG.append(sEPSG)
                wasdi.wasdiLog('Collected EPSG from average tile')

            try:
                if bDelete == True:
                    wasdi.wasdiLog('Cleanup imported products')
                    for sProduct in asProductsAvailable:
                        wasdi.deleteProduct(sProduct + '.zip')
            except Exception as oE:
                wasdi.wasdiLog(f'Error cleaning up imported products: {type(oE)}: {oE}')
                # no need to exit if the cleanup failed

            iNumberProcessedTiles = iNumberProcessedTiles + 1
            iProgressPerc = round( (60 / len(asTiles) ) * iNumberProcessedTiles + 10 )
            wasdi.updateProgressPerc(iProgressPerc)

    except Exception as oE:
        wasdi.wasdiLog(f'Error computing averages {type(oE)}: {oE}')
        wasdi.updateStatus('ERROR', 0)
        sys.exit(oE)


    # average of averages, checking for the appropriate reference system
    try:
        asWorkspaceImages = wasdi.getProductsByActiveWorkspace()
        asAveragesInWorkspace = [s for s in asWorkspaceImages if s in asAverageTiles]

        # eventually reproject the average into the first EPSG:
        # normal in case all tile are in the same EPSG
        # arbitrary choice in case the tiles are in different EPSG

        if (len(asTiles)) == 1:

            # first project the average into WSG84 geographic
            wasdi.wasdiLog('Cropping and projecting tile average into WGS84 geographic')
            oBboxNE = oBbox["northEast"]
            oBboxSW = oBbox["southWest"]
            fLonW = oBboxSW["lng"]
            fLatS = oBboxSW["lat"]
            fLonE = oBboxNE["lng"]
            fLatN = oBboxNE["lat"]
            sBbox = [fLonW, fLatS, fLonE, fLatN]
            # bilinear because of continuous data (tiff_images_average would warp anyways but with the default Alg
            # which is near: nearest neighbour resampling (default, fastest algorithm, worst interpolation quality)
            # gdal.Warp automatically saves to disk
            aoWarpOptions = gdal.WarpOptions(resampleAlg=gdal.gdalconst.GRA_Bilinear,
                                             srcNodata=np.nan,
                                             dstNodata=np.nan,
                                             dstSRS="EPSG:4326",
                                             outputBounds=sBbox,
                                             xRes=0.0001, yRes=-0.0001)  # resolution, in degrees, close to 10m

            sAverageTileNameWGS84 = sAverageTile.replace(".tif", "_WGS84geo.tif")
            oToBeProjected = gdal.Open(wasdi.getPath(sAverageTile))

            # arguments: name of the reprojected dataset (output), dataset to be projected (input), options
            oProjected = gdal.Warp(wasdi.getPath(sAverageTileNameWGS84), oToBeProjected, options=aoWarpOptions)
            wasdi.addFileToWASDI(sAverageTileNameWGS84)
            wasdi.wasdiLog('Cropped projected tile average ' + sAverageTileNameWGS84 + ' in WGS84 geographic added to workspace')

            wasdi.updateProgressPerc(80)

            # then reproject the average into its EPSG
            wasdi.wasdiLog('Projecting tile average into UTM')
            sEPSG = "EPSG:" + asEPSG[0]

            sAverageOfAveragesUTM = sOutputBaseName + "_AverageS2.tif"
            oToBeProjected = gdal.Open(wasdi.getPath(sAverageTileNameWGS84))

            # bilinear because of continuous data (tiff_images_average would warp anyways but with the default Alg
            # which is near: nearest neighbour resampling (default, fastest algorithm, worst interpolation quality)
            # gdal.Warp automatically saves to disk
            aoWarpOptions = gdal.WarpOptions(resampleAlg=gdal.gdalconst.GRA_Bilinear,
                                             srcNodata=np.nan,
                                             dstNodata=np.nan,
                                             dstSRS=sEPSG,
                                             xRes=iXr, yRes=-iYr)
            # arguments: name of the reprojected dataset (output), dataset to be projected (input), options
            oProjected = gdal.Warp(wasdi.getPath(sAverageOfAveragesUTM), oToBeProjected, options=aoWarpOptions)
            wasdi.addFileToWASDI(sAverageOfAveragesUTM)
            wasdi.wasdiLog('Cropped tile average in UTM added to workspace')

            wasdi.deleteProduct(sAverageTileNameWGS84)

            wasdi.updateProgressPerc(90)

        else:
        #if (len(asTiles) > 1):

            # first project all averages into WSG84 geographic
            wasdi.wasdiLog('Cropping and projecting all tile averages into WGS84 geographic')
            oBboxNE = oBbox["northEast"]
            oBboxSW = oBbox["southWest"]
            fLonW = oBboxSW["lng"]
            fLatS = oBboxSW["lat"]
            fLonE = oBboxNE["lng"]
            fLatN = oBboxNE["lat"]
            sBbox = [fLonW, fLatS, fLonE, fLatN]
            # bilinear because of continuous data (tiff_images_average would warp anyways but with the default Alg
            # which is near: nearest neighbour resampling (default, fastest algorithm, worst interpolation quality)
            # gdal.Warp automatically saves to disk
            aoWarpOptions = gdal.WarpOptions(resampleAlg=gdal.gdalconst.GRA_Bilinear,
                                             srcNodata=np.nan,
                                             dstNodata=np.nan,
                                             dstSRS="EPSG:4326",
                                             outputBounds=sBbox,
                                             xRes=0.0001, yRes=-0.0001)  # resolution, in degrees, close to 10m
            asAveragesWGS84 = []
            for sAverageInWorkspace in asAveragesInWorkspace:
                sAverageWGS84 = sAverageInWorkspace.replace(".tif", "_WGS84geo.tif")
                asAveragesWGS84.append(sAverageWGS84)
                oToBeProjected = gdal.Open(wasdi.getPath(sAverageInWorkspace))

                # arguments: name of the reprojected dataset (output), dataset to be projected (input), options
                oProjected = gdal.Warp(wasdi.getPath(sAverageWGS84), oToBeProjected, options=aoWarpOptions)
                wasdi.addFileToWASDI(sAverageWGS84)
                wasdi.wasdiLog('Cropped projected average ' + sAverageWGS84 + ' in WGS84 geographic added to workspace')

            wasdi.updateProgressPerc(80)

            # then average in WGS84
            wasdi.wasdiLog('Computing average of all tile averages in WGS84 geographic')
            sAverageOfAveragesWSG84 = 'Average_all_tiles_WGS84geo.tif'
            if sAverageOfAveragesWSG84 not in asWorkspaceImages:
                # start loop per tile average...
                iProcessedFiles = 0
                for sAverageWGS84 in asAveragesWGS84:
                    oAverageWGS84 = gdal.Open(wasdi.getPath(sAverageWGS84))
                    iRows = oAverageWGS84.RasterYSize
                    iCols = oAverageWGS84.RasterXSize

                    oRasterBand = oAverageWGS84.GetRasterBand(1)
                    afBandAsArray = oRasterBand.ReadAsArray(0, 0, iCols, iRows)
                    oShape = afBandAsArray.shape
                    oShape3D = oShape + (iNumberOfBands,)

                    if oShape[0] * oShape[1] > 100527 * 115126:
                        wasdi.wasdiLog(
                            'trying to allocate a matrix which is rather large, this is likely to fail. Please consider using a smaller bounding box')
                    if oShape3D[0] * oShape3D[1] * oShape3D[2] > 100527 * 115126:
                        wasdi.wasdiLog(
                            'trying to allocate a matrix which is rather large, this is likely to fail. Please consider using a smaller bounding box')

                    if iProcessedFiles == 0:
                        wasdi.wasdiLog(f'allocating array of shape {oShape3D} for bands')
                        # allocate memory
                        afOutputs = np.zeros(oShape3D)
                        afCounts = np.zeros(oShape3D, dtype="int")
                        iProcessedFiles = iProcessedFiles + 1

                    for iBand in range(iNumberOfBands):  # iBand starts from 0
                        oRasterBand = oAverageWGS84.GetRasterBand(iBand + 1)
                        afBandAsArray = oRasterBand.ReadAsArray(0, 0, iCols, iRows)

                        afCounts[:, :, iBand] = np.where(afBandAsArray > 0 & np.isfinite(afBandAsArray),
                                                             afCounts[:, :, iBand] + 1, afCounts[:, :, iBand])
                        afOutputs[:, :, iBand] = np.where(afBandAsArray > 0 & np.isfinite(afBandAsArray),
                                                              afOutputs[:, :, iBand] + afBandAsArray, afOutputs[:, :, iBand])

                        del oRasterBand
                        del afBandAsArray

                    del oAverageWGS84

                oAverageWGS84 = gdal.Open(wasdi.getPath(asAveragesWGS84[0]))
                oDriver = gdal.GetDriverByName("GTiff")
                # inverted iCols and iRows... mah
                oOutAverageOfAverages = oDriver.Create(wasdi.getPath(sAverageOfAveragesWSG84), iCols, iRows,
                                             iNumberOfBands, gdal.GDT_Float32, ['COMPRESS=LZW', 'BIGTIFF=YES'])
                #oOutAverageOfAverages = oDriver.Create(wasdi.getPath(sAverageOfAveragesWSG84), iCols, iRows,
                #                             iNumberOfBands, gdal.GDT_Int32, ['COMPRESS=LZW', 'BIGTIFF=YES'])
                # sets same geotransform as one of the bands
                oOutAverageOfAverages.SetGeoTransform(oAverageWGS84.GetGeoTransform())
                # sets same projection as one of the bands
                oOutAverageOfAverages.SetProjection(oAverageWGS84.GetProjection())

                afAverageBand = np.empty(oShape)  # preinit
                #afAverages[:] = -9999
                afAverageBand[:] = np.nan
                adNan = np.empty(oShape)  # preinit
                #adNan[:] = -9999
                adNan[:] = np.nan
                for iBand in range(iNumberOfBands):  # iBand starts from 0
                    # only divide when denumerator different from adNan
                    afAverageBand = np.divide(afOutputs[:, :, iBand], afCounts[:, :, iBand], out=adNan,
                                                        where=afCounts[:, :, iBand] != 0)
                    # round
                    #afAverages[:, :, iBand] = round(afAverages[:, :, iBand])
                    #afAverages[:, :, iBand] = np.where(afAverages[:, :, iBand] < 0, -9999, afAverages[:, :, iBand] < 0)
                    # write
                    oOutAverageOfAverages.GetRasterBand(iBand + 1).WriteArray(afAverageBand)
                    # Set a no data value if required
                    #oOutAverageOfAverages.GetRasterBand(iBand + 1).SetNoDataValue(-9999)
                    oOutAverageOfAverages.GetRasterBand(iBand + 1).SetNoDataValue(np.nan)

                # time to save to disk
                oOutAverageOfAverages.FlushCache()
                wasdi.addFileToWASDI(sAverageOfAveragesWSG84)
                wasdi.wasdiLog('Average of all tile averages in WGS84 geographic added to workspace')

            wasdi.updateProgressPerc(85)

            # eventually reproject the average into the first EPSG
            wasdi.wasdiLog('Projecting average of all tile averages into UTM')
            sEPSG = "EPSG:" + asEPSG[0]

            sAverageOfAveragesUTM = sOutputBaseName + "_AverageS2.tif"
            oToBeProjected = gdal.Open(wasdi.getPath(sAverageOfAveragesWSG84))

            # bilinear because of continuous data (tiff_images_average would warp anyways but with the default Alg
            # which is near: nearest neighbour resampling (default, fastest algorithm, worst interpolation quality)
            # gdal.Warp automatically saves to disk
            aoWarpOptions = gdal.WarpOptions(resampleAlg=gdal.gdalconst.GRA_Bilinear,
                                             srcNodata=np.nan,
                                             dstNodata=np.nan,
                                             dstSRS=sEPSG,
                                             xRes=iXr, yRes=-iYr)
            # arguments: name of the reprojected dataset (output), dataset to be projected (input), options
            oProjected = gdal.Warp(wasdi.getPath(sAverageOfAveragesUTM), oToBeProjected, options=aoWarpOptions)
            wasdi.addFileToWASDI(sAverageOfAveragesUTM)
            wasdi.wasdiLog('Cropped average of all tile averages in UTM added to workspace')

            if bDelete == True:
                wasdi.deleteProduct(sAverageOfAveragesWSG84)
                for sAverageWGS84 in asAveragesWGS84:
                    wasdi.deleteProduct(sAverageWGS84)

        wasdi.updateProgressPerc(90)

    except Exception as oE:
        wasdi.wasdiLog(f'Error averaging averages')
        wasdi.updateStatus('ERROR', 0)
        sys.exit(oE)


    try:
        if bDelete == True:
            wasdi.wasdiLog('Cleanup tile average')
            # for sProduct in asImagesDownloaded:
            for sAverageTile in asAverageTiles:
                wasdi.deleteProduct(sAverageTile)
    except Exception as oE:
        wasdi.wasdiLog(f'Error cleaning up tile average(s): {type(oE)}: {oE}')
        # no need to exit if the cleanup failed

    ## time elapsed to retrieve data
    #td2 = time.time()

    try:
        wasdi.wasdiLog('Cleanup temporary files')
        sTmpDir.cleanup()
    except Exception as oE:
        wasdi.wasdiLog(f'Error cleaning up temporary files: {type(oE)}: {oE}')
        # no need to exit if the temporary files could not be deleted

    wasdi.updateProgressPerc(95)

    try:
        aoPayload = {
            'input': wasdi.getParametersDict()
        }
        # Save all S2 images of all tiles
        aoPayload["S2_images"] = asProductsAvailableAllTiles
        wasdi.setPayload(aoPayload)
    except Exception as oE:
        wasdi.wasdiLog(f'Error saving/ingesting file: {type(oE)}: {oE}')
        # probably no need to exit if the payload could not be saved


    ## time elapsed to process data
    #tp2 = time.time()
    #wasdi.wasdiLog('Time to search and retrieve data (H:MM:SS): {}'.format(datetime.timedelta(seconds=round(td2 - td1))))
    #wasdi.wasdiLog('Time to process data:            (H:MM:SS): {}'.format(datetime.timedelta(seconds=round(tp2 - td2))))

    wasdi.wasdiLog('Completed')


def applySCL(afCounts, afOutputs, aiSCLAsArray, asBandsWarped, bTestOutTiff, iCols, iProcessedFiles, iRows, oOutTiff,
             oShape3D, sProduct):
    # apply SCL to all other bands
    iIndex = 0
    for sPath in asBandsWarped:
        oBand = gdal.Open(sPath)
        iRows = oBand.RasterYSize
        iCols = oBand.RasterXSize
        oRasterBand = oBand.GetRasterBand(1)
        aiBandAsArray = oRasterBand.ReadAsArray(0, 0, iCols, iRows)

        # https://docs.sentinel-hub.com/api/latest/data/sentinel-2-l2a/
        aiBandAsArray = np.where(aiSCLAsArray == 1, -9999, aiBandAsArray)  # SCL value for Saturated / Defective
        aiBandAsArray = np.where(aiSCLAsArray == 2, -9999, aiBandAsArray)  # Dark Area Pixels
        aiBandAsArray = np.where(aiSCLAsArray == 3, -9999, aiBandAsArray)  # SCL value for Cloud Shadows
        aiBandAsArray = np.where(aiSCLAsArray == 7, -9999,
                                 aiBandAsArray)  # SCL value for Clouds low probability / Unclassified
        aiBandAsArray = np.where(aiSCLAsArray == 8, -9999, aiBandAsArray)  # SCL value for Clouds medium probability
        aiBandAsArray = np.where(aiSCLAsArray == 9, -9999, aiBandAsArray)  # SCL value for Clouds high probability
        aiBandAsArray = np.where(aiSCLAsArray == 10, -9999, aiBandAsArray)  # SCL value for Cirrus
        aiBandAsArray = np.where(aiSCLAsArray == 11, -9999, aiBandAsArray)  # SCL value for Snow / Ice

        if bTestOutTiff == 1:
            oOutTiff.GetRasterBand(iIndex + 1).WriteArray(aiBandAsArray)

        if iProcessedFiles == 0:
            wasdi.wasdiLog(f'allocating array of shape {oShape3D} for bands')
            # allocate memory
            afOutputs = np.zeros(oShape3D)
            afCounts = np.zeros(oShape3D, dtype="int")
            iProcessedFiles = iProcessedFiles + 1

        afCounts[:, :, iIndex] = np.where(aiBandAsArray > 0 & np.isfinite(aiBandAsArray),
                                          afCounts[:, :, iIndex] + 1, afCounts[:, :, iIndex])
        afOutputs[:, :, iIndex] = np.where(aiBandAsArray > 0 & np.isfinite(aiBandAsArray),
                                           afOutputs[:, :, iIndex] + aiBandAsArray, afOutputs[:, :, iIndex])

        iIndex = iIndex + 1
        del oBand
        del oRasterBand
        del aiBandAsArray
        wasdi.wasdiLog('Done cloud masking band ' + str(iIndex) + ' of image ' + sProduct)
    return afCounts, afOutputs, iCols, iRows


def collectBandsPaths(asBands, bInMemory, sProduct):
    # list zip bands content
    try:
        wasdi.wasdiLog('Search bands: {}'.format(asBands))
        asBandsZipped, sSCLZipped = listBandsGivenS2Product(sProduct, asBands)
        wasdi.wasdiLog('Bands (zip) found: {}'.format(len(asBandsZipped)))

        # set working in memory or save intermediate files on disk
        sSavePath = wasdi.getSavePath()
        sTmpDir = tempfile.TemporaryDirectory(dir=sSavePath)
        if bInMemory:
            sWorkPath = sTmpDir.name.replace(sSavePath, '/vsimem/')
        else:
            sWorkPath = sTmpDir.name

        wasdi.wasdiLog('Set temporary files to: {}'.format(sWorkPath))
    except Exception as oE:
        wasdi.wasdiLog(f'Error listing bands: {type(oE)}: {oE}')
        wasdi.updateStatus('ERROR', 0)
        sys.exit(oE)
    return asBandsZipped, sSCLZipped, sTmpDir, sWorkPath


def warp(asBandsZipped, iXr, iYr, sSCLZipped, sWorkPath):
    # warp
    try:
        wasdi.wasdiLog('Start warping image to VRTs')
        asBandsWarped, sSCLWarped = warpBands(asBandsZipped, sSCLZipped, sWorkPath, iXr, iYr)
        wasdi.wasdiLog('Warp to VRTs done')
    except Exception as oE:
        wasdi.wasdiLog(f'Error warping: {type(oE)}: {oE}')
        wasdi.updateStatus('ERROR', 0)
        sys.exit(oE)
    return asBandsWarped, sSCLWarped


def getTiles(aoS2L2Images, asTiles):
    # get the list of tiles from the S2 names
    try:
        if asTiles == None:
            asTiles = []
            for oS2L2Image in aoS2L2Images:
                sImage = oS2L2Image["title"]
                sTile = sImage.split('_')[5]
                if sTile not in asTiles:
                    asTiles.append(sTile)

    except Exception as oE:
        wasdi.wasdiLog(f'Error listing the tiles: {type(oE)}: {oE}')
        wasdi.updateStatus('ERROR', 0)
        sys.exit(oE)
    wasdi.wasdiLog('List of tiles: ' + ' ,'.join(asTiles))
    wasdi.updateProgressPerc(10)
    return asTiles


def searchImages(oBbox, sEndDate, sProvider, sStartDate):
    # search products
    try:
        sProductType = 'S2MSI2A'
        wasdi.wasdiLog('Search products: {}'.format(sProductType))
        wasdi.wasdiLog('From: {}'.format(sStartDate))
        wasdi.wasdiLog('Till: {}'.format(sEndDate))
        aoS2L2Images = wasdi.searchEOImages(
            "S2",
            sProductType="S2MSI2A",
            sDateFrom=sStartDate, sDateTo=sEndDate,
            oBoundingBox=oBbox,
            sProvider=sProvider
        )
        wasdi.updateProgressPerc(5)

        if len(aoS2L2Images) <= 0:
            wasdi.wasdiLog("No images found")
            wasdi.updateStatus("DONE", 100)
            sys.exit(0)

    except Exception as oE:
        wasdi.wasdiLog(f'Error searching data: {type(oE)}: {oE}')
        wasdi.updateStatus('ERROR', 0)
        sys.exit(oE)
    return aoS2L2Images


def listBandsGivenS2Product(sProduct, asBands):
    try:
        sZipFileName = wasdi.getFullProductPath(sProduct + '.zip')

        asBandsJp2 = [sBand + '.jp2' for sBand in asBands]
        asBandsZip = []
        sSCLPath = ''
        #for zip_name in sZipName:
        with zipfile.ZipFile(sZipFileName, 'r') as zf:
            asAllPaths = zf.namelist()
            asBandPaths = [sName for sBand in asBandsJp2 for sName in asAllPaths if sBand in sName]

            sSCLPath = next((sPath for sPath in asAllPaths if 'SCL_20m' in sPath), None)

        asBandsZip = ['/vsizip/' + sZipFileName + '/' + sBand for sBand in asBandPaths]
        #asBandsZip.extend(asBandsZip)

        sSCLZip = '/vsizip/' + sZipFileName + '/' + sSCLPath

        return asBandsZip, sSCLZip
    except Exception as oE:
        wasdi.wasdiLog(f'Error in list_s2_bands: {type(oE)}: {oE}')
        return None



def warpBands(asBandsZip, sSCLZip, sWP, iXres, iYres):
    wasdi.wasdiLog('starting bands warp...')
    try:
        wasdi.wasdiLog('Getting the spatial resolution')
        sResolutionPath = next((s for s in asBandsZip if f'_{iXres}m.jp2' in s), None)
        if sResolutionPath is not None:
            oResolutionDataset = gdal.Open(sResolutionPath)
            ulx, iXres, xskew, uly, yskew, iYres = oResolutionDataset.GetGeoTransform()

        wasdi.wasdiLog('Warping all bands given in input')
        asBandsWarpedVRT = []
        for sBandZip in asBandsZip:
            if f'_{iXres}m.jp2' in sBandZip:
                asBandsWarpedVRT.append(sBandZip)
            else:
                sBandVRT = path.join(sWP, path.basename(sBandZip).replace('.jp2', '.vrt'))
                gdal.Warp(sBandVRT, sBandZip, format='VRT', resampleAlg='bilinear', xRes=iXres, yRes=iYres)
                asBandsWarpedVRT.append(sBandVRT)

        sSCLWarpedVRT = path.join(sWP, path.basename(sSCLZip).replace('.jp2', '.vrt'))
        gdal.Warp(sSCLWarpedVRT, sSCLZip, format='VRT', resampleAlg='near', xRes=iXres, yRes=iYres)

        wasdi.wasdiLog('Bands warped')
        return asBandsWarpedVRT, sSCLWarpedVRT
    except Exception as oE:
        wasdi.wasdiLog(f'Error in warp_bands: {type(oE)}: {oE}')
        return None


if __name__ == '__main__':
    wasdi.init('./config.json')
    run()
