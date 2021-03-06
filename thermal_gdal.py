#! /usr/bin/env python

#######################################
# GDALCalcNDVI.py
#
# A script using the GDAL Library to
# create a new image contains the NDVI
# of the original image
#
# Author: <YOUR NAME>
# Email: <YOUR EMAIL>
# Date: DD/MM/YYYY
# Version: 1.0
#######################################

# Import required libraries from python
import sys, os, struct, glob, numpy, math
# Import gdal
import osgeo.gdal as gdal

# Define the class GDALCalcNDVI
class GDALCalcLST (object):

    # A function to create the output image
    def createOutputImage(self, outFilename, inDataset):
        # Define the image driver to be used
        # This defines the output file format (e.g., GeoTiff)
        driver = gdal.GetDriverByName( "GTiff" )
        # Check that this driver can create a new file.
        metadata = driver.GetMetadata()
        if metadata.has_key(gdal.DCAP_CREATE) and metadata[gdal.DCAP_CREATE] == 'YES':
            print 'Driver GTiff supports Create() method.'
        else:
            print 'Driver GTIFF does not support Create()'
            sys.exit(-1)
        # Get the spatial information from the input file
        geoTransform = inDataset.GetGeoTransform()
        geoProjection = inDataset.GetProjection()
        # Create an output file of the same size as the inputted
        # image but with only 1 output image band.
        newDataset = driver.Create(outFilename, inDataset.RasterXSize, \
                     inDataset.RasterYSize, 1, gdal.GDT_Float32)
        # Define the spatial information for the new image.
        newDataset.SetGeoTransform(geoTransform)
        newDataset.SetProjection(geoProjection)
        return newDataset

    # The function which loops through the input image and
    # calculates the output LST value to be generated.
    def calcLST(self, filePath,outFilePath,radianceup,radiancedown,lmin,lmax): ##, outFilePath after filepath

        # Open the inputted dataset
        dataset = gdal.Open( filePath, gdal.GA_ReadOnly )

        # Check the dataset was successfully opened
        if dataset is None:
            print "The dataset could not opened"
            sys.exit(-1)

        # Create the output dataset and file path
        ##outFilePath = filePath + '\\' + 'results'
        ##if not os.path.exists(outFilePath): os.makedirs(outFilePath)
        outDataset = self.createOutputImage(outFilePath, dataset)

        # Check the datasets was successfully created.
        if outDataset is None:
            print 'Could not create output image'
            sys.exit(-1)

        # Opens data from the sensor
        band = dataset.GetRasterBand(1) # Input thermal band

        # Retrieve the number of lines within the image
        numLines = band.YSize
        # Loop through each line in turn.
        for line in range(numLines):
            # Define variable for output line.
            outputLine = ''
            # Read in data for the current line from the
            # image band representing the red wavelength
            band_scanline = band.ReadRaster( 0, line, band.XSize, 1, \
                           band.XSize, 1, gdal.GDT_Float32 )
            # Unpack the line of data to be read as floating point data
            band_tuple = struct.unpack('f' * band.XSize, band_scanline)

            # Loop through the columns within the image
            for i in range(len(band_tuple)):
                # Calculate the TOA Radiance for the current pixel.
                qcalmax = 255     # Given
                qcalmin = 1       # Given
                TOA = 0
                TOA = (((lmax - lmin) / (qcalmax - qcalmin)) * (band_tuple[i] \
                - qcalmin)) + lmin

                # Converts top-of-atmosphere radiance to surface-leaving radiance
                emissivity = 0.95       # emissivity from the YALE paper
                transmissivity = 0.66   # transmissivity from the YALE paper

                SLR = ((TOA - radianceup)/(emissivity * transmissivity)) - \
                ((1 - emissivity) / (emissivity)) * radiancedown
                
                # Converts SLR results to just above 0 if negative or = 0. This is
                # because math.log cannot be run on 0 or - numbers. 
                if SLR <= 0:
                   SLR = 0.0001
                else:
                     SLR = SLR

                # Converts top-of-atmosphere radiance to Temperature in Kelvin
                k1 = 607.76
                k2 = 1260.56
                tempkelvin = k2 / math.log((k1/SLR)+1)
                # Becareful of zero divide
                

                # Add the current pixel to the output line
                outputLine = outputLine + struct.pack('f', tempkelvin)
            # Write the completed line to the output image
            outDataset.GetRasterBand(1).WriteRaster(0, line, band.XSize, 1, \
                                            outputLine, buf_xsize=band.XSize,
                                            buf_ysize=1, buf_type=gdal.GDT_Float32)
            # Delete the output line following write
            del outputLine
        print 'LST Calculated and output to file'


    # The function from which the script runs.
    def run(self):
        filePath = "D:\Landsat Downloader\Downloads\LE70290302002347EDC00.tar\LE70290302002347EDC00\LE70290302002347EDC00_B6_VCID_1.TIF"  # Location of directory of images
        outFilePath = 'D:\Landsat Downloader\Downloads\LE70290302002347EDC00.tar\LE70290302002347EDC00\lst_k.tif'
        radianceup = 2.2
        radiancedown = 4.2
        lmin = 1.50
        lmax = 15.0
        # Check the input file exists
        if os.path.exists(filePath):
            # Run calcNDVI function
            self.calcLST(filePath,outFilePath,radianceup,radiancedown,lmin,lmax)
        else:
            print 'The file does not exist.'

# Start the script by calling the run function.
if __name__ == '__main__':
    obj = GDALCalcLST()
    obj.run()
