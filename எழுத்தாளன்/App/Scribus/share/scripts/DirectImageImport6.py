#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 

Diese Skript importiert ein Bild und setzt es auf die akutelle Seite.
Der Bildrahmen wird dem Bild angepasst und in den nicht-proportionalen Modus
gesetzt, das heisst, beliebige Verzerrungen sind moeglich.

Um das Bild proportional zu vergroessern, die STRG-Taste beim Bearbeiten druecken.

Tested with scribus 1.3.3.3

Author: Konrad Stania

Some modifications 2009 by Gregory Pittman, tested on Scribus 1.3.3.13svn

This newer version uses the Python Imaging Library to get the dimensions of the
image to be imported, and adjusts the frame accordingly. Initially the frame will
be created centered, at 80% of the page's width or height, whichever is smaller. 
There is an adjustment to 80% of the height of the page in case this is exceeded 
by the initial calculation.

USAGE:

You must have a document open. Run the script, a dialog asks you to choose an
image to load. A proportional frame is automatically created and image loaded, 
then adjusted to frame size.

Major modifications February 2020 by Mike Crane tested on Scribus 1.5.5, Windows10, Python 3.8

Builds on 2009 version
Translation of german variable names, comments, Tkinter, Multiple image management, code tidying

USAGE:

You must have a document open. Run the script, a dialog asks you to choose the number of
images in a 'row' (arbitrary max of 4). A Second dialog asks you to choose a number of 'rows'
(max 4 on a portrait page, 2 on a landscape page).  A succession of file dialogs then ask you to
choose one or more images to load. Frames are automatically created, sized and placed according to
the available space and maintaining the image aspect ratio.  Images are loaded, and adjusted to frame size, until all
rows and columns are filled OR cancel is pressed in the file dialog.

LICENSE:

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
name
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
"""

# Craig Bradney, Scribus Team.

# 10/3/08: Added to Scribus 1.3.3.12svn distribution "as was" from Scribus wiki for bug #6826, script is GPLd

# Imports
import sys

try:
    import scribus
    
except ImportError:
    print ("This script only runs from within Scribus.")
    sys.exit(1)
    
# MUST import tkinter before PIL to avoid namespace clash
# because both modules have image class
try:
    from Tkinter import *
    import tkMessageBox
    import tkFileDialog
except ImportError:
    scribus.messageBox("Script failed","Script requires Tkinter properly installed.",scribus.ICON_CRITICAL)
    sys.exit(1)
    
try:
    from PIL import Image
except ImportError:
    scribus.messageBox("PIL","Unable to import the Python Imaging Library module.",scribus.ICON_CRITICAL)
    sys.exit(1)

def main():
    # Constants
    # Change these to suit user
    # default start point for file dialog
    # imagePath = "/home/mike/Pictures"
    imagePath = "c:/users/mike/pictures"
    scalingFactor = 0.8
    framefillColour = "none"
    framelineColour = "none"
    
    # Get/set page related variables
    # page size
    pageX,pageY = scribus.getPageSize()
    # pageX is page width (Portrait AND Landscape)
    # pageY is page height

    # page margins - Top, Left, Right, Bottom
    marginT,marginL,marginR,marginB = scribus.getPageMargins()
    
    # set up variables for 'working' area
    # i.e. area inside margins
    workingwidth = pageX - marginL - marginR
    workingheight = pageY - marginT - marginB
    # scribus.messageBox("Image Import", "Working Width: " + str(workingwidth)  + "\nWorking height: " + str(workingheight), scribus.ICON_INFORMATION)
    
    root = Tk()
    # we don't want a full GUI, so kill the root window
    root.withdraw()
    
    # User input for images per row
    imageCountH = scribus.valueDialog('Horizontal Sizing','How many images side by side (min 1, max 4)?','2')
    if (not imageCountH):
        sys.exit(1)

    imageCountH = int(imageCountH)
     
    if imageCountH < 1 or imageCountH > 4:
        scribus.messageBox("Horizontal Sizing","I said min 1 & max 4 - what's wrong with you!.",scribus.ICON_WARNING,scribus.BUTTON_OK)
        sys.exit(1)

    # set up messages & defaults for image rows dialog
    # depending on page orientation
    if pageX > pageY:
        # landscape page - max 2 rows
        msgboxText = "How many rows of images (min 1, max 2)?"
        if imageCountH == 1:
            msgboxDefault = str(imageCountH)
        else:
            msgboxDefault = "2" 
    else:
        # portrait page
        msgboxText = "How many rows of images (min 1, max 4)?"
        msgboxDefault = str(imageCountH)   
            
    # User input for image rows
    imageCountV = scribus.valueDialog('Vertical Sizing',msgboxText,msgboxDefault)
    if (not imageCountV):
        sys.exit()

    imageCountV = int(imageCountV)
     
    # row input validation
    if imageCountV < 1:
        scribus.messageBox("Vertical Sizing","I said min 1 - what's wrong with you!.",scribus.ICON_WARNING,scribus.BUTTON_OK)
        sys.exit(1)

    # max value for rows depends on page orientation
    if pageX < pageY and imageCountV > 4:
        # portrait
        scribus.messageBox("Vertical Sizing","Portrait page - can't have more than 4 rows of images!.",scribus.ICON_WARNING,scribus.BUTTON_OK)
        sys.exit(1)

    # landscape - max 2 rows
    if pageX > pageY and imageCountV > 2:
        scribus.messageBox("Vertical Sizing","Landscape page - can't have more than 2 rows of images!.",scribus.ICON_WARNING,scribus.BUTTON_OK)
        sys.exit(1)

    # scribus.messageBox("Image Count","Cols - imageCountH: " + str(imageCountH) + " Rows - imageCountV: " + str(imageCountV),scribus.ICON_INFORMATION)
    # calculate the size of the notional 'cells' that the page is now divided into
    cellwidth=workingwidth/imageCountH
    cellheight = workingheight/imageCountV
    # calculate the cell aspect ratio
    cellAspectratio = cellwidth/cellheight
    
    # Build the columns in each row
    # need to start loops at 0 for autocalc of col & row position
    rowCounter = 0
    while rowCounter < imageCountV:
        # loop through rows
        colCounter = 0
        while colCounter < imageCountH:
            # loop through columns
            # Get the image file name from dialog            
            ImageFileName = tkFileDialog.askopenfilename(initialdir = imagePath,title="Image Import")
        
            # trap cancel in Filedialog - Cancel returns empty string
            if not ImageFileName:
                sys.exit(1)

            # open image & get its width & height 
            im = Image.open(ImageFileName)        
            xsize, ysize = im.size
            # need to type the image size variables to
            # calculate the aspect ratio
            # Without typing, result always zero!
            imageWidth = float(xsize)
            imageHeight = float(ysize)
            imageAspectratio = float(imageWidth/imageHeight)

            # scribus.messageBox("Image Info", "Image width: " + str(xsize)  + "\nImage height: " + str(ysize)+ "\nImage AR: " + str(imageAspectratio), scribus.ICON_INFORMATION)    
            
            if imageAspectratio > cellAspectratio:
                # Width is limiting dimension, so
                # calculate optimum frame WIDTH by dividing working width equally.
                # Then apply default scalingFactor (Constant) to give a margin between images   
                FrameWidth = (workingwidth/imageCountH) * scalingFactor 

                # With width fixed, scale frame height to keep aspect ratio of original image
                FrameHeight = FrameWidth/imageAspectratio
                # scribus.messageBox("Image AR > Cell AR", "Image AR: " + str(imageAspectratio)  + "\nCell AR: " + str(cellAspectratio), scribus.ICON_INFORMATION)
            
            else:
                # For images with aspect ratio < cell aspect ratio
                # Height is limiting dimension, so
                # we want to apply scalingFactor to limit HEIGHT of frame.
                # so we first calculate optimum Frame Height, then scale width from height
                FrameHeight = (workingheight/imageCountV) * scalingFactor
                FrameWidth = FrameHeight * imageAspectratio
                # scribus.messageBox("Image AR < Cell AR", "Image AR: " + str(imageAspectratio)  + "\nCell AR: " + str(cellAspectratio), scribus.ICON_INFORMATION)
 
            # Calculate internal vertical margin (gutter) between frames
            internalVMargin = (workingwidth - (FrameWidth*imageCountH))/(imageCountH+1)

            # Calculate internal horizontal margin (gutter) between frames
            internalHMargin = (workingheight - (FrameHeight*imageCountV))/(imageCountV+1) 

            # Calculate column positions
            coordX = marginL + internalVMargin + ((FrameWidth + internalVMargin) * colCounter)

            # Calculate row positions
            coordY = marginT + internalHMargin + ((FrameHeight + internalHMargin) * rowCounter) 
            
            #build and load frames
            #===================================================================
            # msg=tkMessageBox.showinfo("Image Import: ", '\
            # \n Page Width=                 ' + str(pageX)  + '\
            # \n Frame Width=                ' + str(FrameWidth)+ '\
            # \n Frame Height=               ' + str(FrameHeight)  + '\
            # \n Internal Vertical Margin=   ' + str(internalVMargin)+ '\
            # \n Internal Horizontal Margin= ' + str(internalHMargin)  + '\
            # \n Horizontal position=        ' + str(coordX)+ '\
            # \n Vertical position=          ' + str(coordY) + '\n')
            #===================================================================
            ImageFrame = scribus.createImage( coordX , coordY, FrameWidth, FrameHeight) 
            scribus.loadImage(ImageFileName, ImageFrame)
            # This shouldn't change the aspect ratio or crop the image because
            # the frame was built to suit the image aspect ratio
            # IF the image IS messed up/distorted, strong chance it was rotated!
            # i.e. it looks landscape but is actually portrait.
            # This needs to be fixed externally in e.g. GIMP
            scribus.setScaleImageToFrame(True, False,ImageFrame)
            
            # use the Constants to set Frame background & outline
            # default is "none"
            scribus.setFillColor(framefillColour, ImageFrame)
            scribus.setLineColor(framelineColour, ImageFrame)
            colCounter = colCounter+1
        rowCounter = rowCounter + 1

def main_wrapper(argv):
    """The main_wrapper() function disables redrawing, sets a sensible generic
    status bar message, and optionally sets up the progress bar. It then runs
    the main() function. Once everything finishes it cleans up after the main()
    function, making sure everything is sane before the script terminates."""
    try:
        scribus.statusMessage("Running script...")
        scribus.progressReset()
        main()
    finally:
        # Exit neatly even if the script terminated with an exception,
        # so we leave the progress bar and status bar blank and make sure
        # drawing is enabled.
        if scribus.haveDoc():
            scribus.setRedraw(True)
        scribus.statusMessage("")
        scribus.progressReset()
    
if __name__ == '__main__':
    if scribus.haveDoc() > 0:
        main_wrapper(sys.argv)
    else:
        scribus.messageBox("Image Import", "You need to have a document open <i>before</i> you can run this script successfully.", scribus.ICON_INFORMATION)
