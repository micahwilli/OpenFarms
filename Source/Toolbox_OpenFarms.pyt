import arcpy
import os
import ConfigParser     #Python 3(ArcGIS Pro) uses configparser. Would probably cause an error
import collections
import itertools
import csv
import re
import string
import traceback

#Two global variables: configFile_old_OpenFarms and configFile_old_Settings. Used to change parameters only if new config file is opened. Did not work as class variables.


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [OpenFarms,Settings]


class OpenFarms(object):

    #p is a dictionary with class scope. The numbers are used as indexes for the parameters list. For example, parameters[self.p['OPEN_CONFIG']] is the same as parameters[0].
    #This was done to make modifying the parameters easier. If the order or number of parameters are changed, they need to be changed here AND in the getParameterInfo() method. getParameterInfo() initializes parameters, so it is separate from the other methods
    #0 should correspond to p0, 1 to p1, etc.
    p = {'OPEN_CONFIG':0,'PARCEL_LAYER':1, 'MANUAL_ACREAGE':2, 'LANDUSE_LAYER':3,'SOIL_LAYER':4,'PARCEL_ID_FIELD':5,'LANDUSE_FIELD':6,'SOIL_FIELD':7,'OUTPUT_FOLDER':8,'FILE_NAME':9}
    read_config_error = False   #Used to set warning message if config file failed to load. Has class scope because it is used by two methods

    #Put class variables above, not in __init__
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "OpenFarms"
        self.description = ""
        self.canRunInBackground = False

    #THIS METHOD ONLY RUNS THE FIRST TIME THE TOOL IS OPENED UNTIL ARCMAP IS RESTARTED. Initial parameters from the config file need to be determined in updateParameters() because it runs every time the tool is opened.
    #Otherwise, the settings tool will not affect OpenFarms until arcmap is restarted
    #To create new parameter: enter new p# and add it to params list at end of method. The order in the params list is the display order, except for categories, which are alphabetical. ALSO modify p dictionary above.
    def getParameterInfo(self):
        """Define parameter definitions"""

        p0 = arcpy.Parameter(
            displayName = 'Open Config File',   #What the user sees in the tool dialog box
            name = 'config_read',               #Must be different than all other parameter names in the tool
            datatype = 'DETextfile',            #Gives error message if input is incorrect data type
            parameterType = 'Optional',         #Required or Optional
            direction = 'Input')                #Input or Output

        p1 = arcpy.Parameter(
            displayName = 'Input Parcel Layer',
            name = 'parcel_layer',
            datatype = 'GPFeatureLayer',
            parameterType = 'Required',
            direction = 'Input')

        p2 = arcpy.Parameter(
            displayName = 'Manual Acreage',
            name = 'manual_acreage',
            datatype = 'GPDouble',
            parameterType = 'Optional',
            direction = 'Input')
        p2.enabled = 0  #disable manual acreage unless 1 parcel is selected (checked in updateMessages)

        p3 = arcpy.Parameter(
            displayName = 'Input Land Use Layer',
            name = 'landuse_layer',
            datatype = 'GPFeatureLayer',
            parameterType = 'Required',
            direction = 'Input')

        p4 = arcpy.Parameter(
            displayName = 'Input Soil Layer',
            name = 'soil_layer',
            datatype = 'GPFeatureLayer',
            parameterType = 'Required',
            direction = 'Input')

        p5 = arcpy.Parameter(
            displayName = 'Parcel ID Field',
            name = 'parcel_field',
            datatype = 'Field',
            parameterType = 'Required',
            direction = 'Input')
        p5.filter.list = ['Short','Long','Float','Single','Double','Text']
        p5.parameterDependencies = [p1.name]    #field names from parcel layer are available to be selected

        p6 = arcpy.Parameter(
            displayName = 'Land Use Field',
            name = 'landuse_field',
            datatype = 'Field',
            parameterType = 'Required',
            direction = 'Input')
        p6.filter.list = ['Short','Long','Float','Single','Double','Text']
        p6.parameterDependencies = [p3.name]

        p7 = arcpy.Parameter(
            displayName = 'Soil Type Field',
            name = 'soil_field',
            datatype = 'Field',
            parameterType = 'Required',
            direction = 'Input')
        p7.filter.list = ['Short','Long','Float','Single','Double','Text']
        p7.parameterDependencies = [p4.name]

        p8 = arcpy.Parameter(
            displayName = 'Output Folder',
            name = 'output_folder',
            datatype = 'DEFolder',
            parameterType = 'Required',
            direction = 'Input')

        p9 = arcpy.Parameter(
            displayName = 'File Name (no extension)',
            name = 'file_name',
            datatype = 'GPString',
            parameterType = 'Required',
            direction = 'Input')
        p9.value = 'output'     #default value


        params = [p0,p1,p2,p3,p4,p5,p6,p7,p8,p9]   #Don't forget to add parameters here!
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    #This method runs every time a parameter is changed. It also runs when the tool is opened. DO ALL INITIAL CONFIG FILE READING HERE, not in getParameterInfo().
    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        global configFile_old_OpenFarms
        #This if statement will only be true when the tool is first opened, because OPEN_CONIFG is given a value inside it. Used for reading last used settings
        if (not parameters[self.p['OPEN_CONFIG']].value) and ( not parameters[self.p['OPEN_CONFIG']].altered):
            configFile_location = os.path.join(os.path.dirname(__file__),'config_location.txt') #Path to location config file that contains path to main config. Must be in same folder as toolbox
            config=ConfigParser.RawConfigParser()
            config.optionxform = str        #Makes config file case-sensitive. Causes problems if not included
            config.read(configFile_location)

            parameters[self.p['OPEN_CONFIG']].value = config.get('DEFAULT','Location')  #get location of last-used config file

            if parameters[self.p['OPEN_CONFIG']].valueAsText is None:       #Should only be true the first time the tool is run. config_default.txt is located in same folder and packaged with add-in
                config_path = os.path.join(os.path.dirname(__file__),'config_default.txt')
                config=ConfigParser.RawConfigParser()
                config.optionxform = str
                config.set('DEFAULT','Location',config_path)
                with open(configFile_location, 'w') as configfile:
                    config.write(configfile)
                parameters[self.p['OPEN_CONFIG']].value = config_path

            configFile_old_OpenFarms = parameters[self.p['OPEN_CONFIG']].valueAsText    #Remember current config file to decide if value changes later
            self.ReadConfig(parameters[self.p['OPEN_CONFIG']].valueAsText,parameters)   #Method that reads the config file, defined below. Different for each class.

        #Read config file if user has changed OPEN_CONFIG parameter. Altered property does not help because it remains true after being changed once
        if configFile_old_OpenFarms != parameters[self.p['OPEN_CONFIG']].valueAsText:
           self.ReadConfig(parameters[self.p['OPEN_CONFIG']].valueAsText,parameters)
           configFile_old_OpenFarms = parameters[self.p['OPEN_CONFIG']].valueAsText

        return

    #Runs after updateParameters(). Any warnings or errors could conflict with internal errors, which probably take precedence. All messages must be written here.
    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        arcpy.env.overwriteOutput = True    #prevents error message if output already exists

        #Simple check to see if file name is valid. Checks for invalid characters for Windows. This is not a rigorous test.
        if any(i in parameters[self.p['FILE_NAME']].valueAsText for i in '<>:"/\|?*'):
            parameters[self.p['FILE_NAME']].setErrorMessage('File name contains invalid characters')

        #True if there is an error in reading config file. Set in ReadConfig() method
        if self.read_config_error:
            parameters[self.p['OPEN_CONFIG']].setWarningMessage('Config file did not load or could not be found. Choose another file or create a new one using settings.')

        #Determines number of tax parcels that are selected in order to inform user about long processing or unavailable manual acreage
        try:
            desc=arcpy.Describe(parameters[self.p['PARCEL_LAYER']].value)   #only determines selection for the specified parameter
            selected_parcels = desc.FIDSet      #String of object IDs of selected features in layer, separated by semicolons
            length = len(selected_parcels.split(';'))   #Separates string into list. Length of list is number of features selected

            if length > 1 or selected_parcels == '': #Either no parcels are selected, or more than one
                if selected_parcels == '':           #Null selection still has length = 1
                    parameters[self.p['PARCEL_LAYER']].setWarningMessage('No parcels in this layer are selected. Process will be run for all parcels.')
                    parameters[self.p['MANUAL_ACREAGE']].setWarningMessage('No parcels are selected. Manual deeded acreage is only available with 1 parcel selected.')
                else:
                    parameters[self.p['MANUAL_ACREAGE']].setWarningMessage('{0} parcels are selected. Manual deeded acreage is only available with 1 parcel selected.'.format(length))
                parameters[self.p['MANUAL_ACREAGE']].enabled = 0

            else:
                parameters[self.p['MANUAL_ACREAGE']].enabled = 1
        except:
            parameters[self.p['PARCEL_LAYER']].setWarningMessage('Parcel selection could not be determined. Make sure correct parcels are selected.')
            parameters[self.p['MANUAL_ACREAGE']].setWarningMessage('Parcel selection could not be determined. Make sure correct parcels are selected.')
            parameters[self.p['MANUAL_ACREAGE']].enabled = 1

        #Warn user if landuse polygons are selected.
        try:
            desc = arcpy.Describe(parameters[self.p['LANDUSE_LAYER']].value)
            selected_landuse = desc.FIDSet

            if selected_landuse != '':
                parameters[self.p['LANDUSE_LAYER']].setWarningMessage('Landuse polygons are selected. Only select parcel layer to avoid unexpected results.')
        except:
            parameters[self.p['LANDUSE_LAYER']].setWarningMessage('Landuse layer selection could not be determined. Make sure no landuse polygons are selected.')

        #Warn user if soil polygons are selected.
        try:
            desc = arcpy.Describe(parameters[self.p['SOIL_LAYER']].value)
            selected_landuse = desc.FIDSet

            if selected_landuse != '':
                parameters[self.p['SOIL_LAYER']].setWarningMessage('Soil polygons are selected. Only select parcel layer to avoid unexpected results.')
        except:
            parameters[self.p['SOIL_LAYER']].setWarningMessage('Soil layer selection could not be determined. Make sure no soil polygons are selected.')

        return

    #Runs after you press OK in the tool dialog
    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            #in_memory feature class locations
            outTemp   = "in_memory/Temp"
            outTemp2  = "in_memory/Temp2"
            outTemp3  = "in_memory/Temp3"
            outFinal  = "in_memory/Final"
            outAllFields = "in_memory/outAllFields"
            outOverlap   = "in_memory/outOverlap"
            inParcels_inmemory = "in_memory/inParcels"
            #Clean temporary memory. If this is not done at the beginning of the script, there will be errors if the layer already exists
            arcpy.Delete_management(outTemp)
            arcpy.Delete_management(outTemp2)
            arcpy.Delete_management(outTemp3)
            arcpy.Delete_management(outAllFields)
            arcpy.Delete_management(outFinal)
            arcpy.Delete_management(outOverlap)
            arcpy.Delete_management(inParcels_inmemory)

            #Parameters included in tool dialog
            open_config = parameters[self.p['OPEN_CONFIG']].valueAsText

            inParcels = parameters[self.p['PARCEL_LAYER']].valueAsText
            manual_acreage = parameters[self.p['MANUAL_ACREAGE']].value     #double
            inLandUse = parameters[self.p['LANDUSE_LAYER']].valueAsText
            inSoil = parameters[self.p['SOIL_LAYER']].valueAsText

            field_parcel_ID = parameters[self.p['PARCEL_ID_FIELD']].valueAsText
            field_land_use = parameters[self.p['LANDUSE_FIELD']].valueAsText
            field_soil_type = parameters[self.p['SOIL_FIELD']].valueAsText

            outFolder = parameters[self.p['OUTPUT_FOLDER']].valueAsText
            fileName = parameters[self.p['FILE_NAME']].valueAsText

            field_gis_acreage_output = 'GISAcreage'  #created for shapefile result
            field_deeded_acreage_output = 'DeededAcre'  #Note: can't add field alias to shapefile. Only first 10 characters will appear in name

            arcpy.CopyFeatures_management(inParcels,inParcels_inmemory) #Use in_memory for faster geoprocessing. Copying soil and land use will not be faster because of large size (only selected parcels are copied).

            #Default values. Used if config file read fails
            bool_use_deeded = 'false'
            field_deeded_acres = ''
            bool_use_flood = 'false'
            flood_layer = ''
            flood_field = ''
            bool_csv = 'true'
            bool_txt = 'true'
            headings_csv = ['ParcelID','Parcel ID','LandUse','Land Use','SoilType','Soil Type','Acres','Acres']         #[option,value,option,value, etc.] Options only needed if config file is used.
            land_use_codes = ['CR','1','PP','2','OF','3','CW','4','NCW','5','ROW','6','NA','6','HS','7','DEFAULT','X']  #[field_value,output_code,field_value,output_code, etc.]

            #Read config file
            #Used for options not shown as parameters
            try:
                config=ConfigParser.RawConfigParser()
                config.optionxform = str

                config.read(open_config)
                try:
                    bool_use_deeded = config.get('FIELDS','UseDeeded')
                    field_deeded_acres = config.get('FIELDS','DeededAcres')
                except:
                    arcpy.AddWarning('Deeded Acreage did not load correctly from config file. Using default values')
                try:
                    bool_use_flood = config.get('FLOOD_DEBASEMENT','UseFloodDebasement')
                    flood_layer = config.get('FLOOD_DEBASEMENT','FloodDebasementLayer')
                    flood_field = config.get('FLOOD_DEBASEMENT','FloodDebasementField')
                except:
                    arcpy.AddWarning('FLOOD_DEBASEMENT section did not load correctly from config file. Using default values')
                try:
                    bool_csv = config.get('OUTPUT','WriteCSV')
                    bool_txt = config.get('OUTPUT','WriteTXT')
                    bool_shapefile = config.get('OUTPUT','WriteShapefile')
                except:
                    arcpy.AddWarning('OUTPUT section did not load correctly from config file. Using default values')
                try:
                    headings_csv_config = config.items('HEADINGS')
                    headings_csv_config = list(itertools.chain(*headings_csv_config))   #Creates list from HEADINGS section: [option,value,option,value, etc.]
                    if len(headings_csv_config) == len(headings_csv):
                        headings_csv = headings_csv_config
                    else:
                        arcpy.AddWarning('HEADINGS section of config file contains incorrect number of entries (should be 4). Using default values')
                except:
                        arcpy.AddWarning('HEADINGS did not load correctly from config file. Using default values')
                try:
                    land_use_codes_config = config.items('LANDUSE_CODES')
                    land_use_codes = list(itertools.chain(*land_use_codes_config))
                except:
                    arcpy.AddWarning('LANDUSE_CODES did not load correctly from config file. Using default values')
            except:
                arcpy.AddWarning('Config file could not be read. Using default values. Please run Settings tool')
                self.PrintError()

            #Create file paths from folder and base file name
            outCSV = os.path.join(outFolder, fileName + '.csv')
            outTXT = os.path.join(outFolder, fileName + '.txt')

            #Second check to see if no parcels are selected. Not really necessary, but helps if someone missed the first warning and is getting angry.
            try:
                desc=arcpy.Describe(inParcels)
                if desc.FIDSet=='':             #if selection is null
                    arcpy.AddWarning('Warning: No parcels are selected. Process will be run for all parcels.')
            except: pass

            #Field map to determine fields copied to the output. Without this, many unnecessary fields are included from each Intersect.
            fm_parcels = arcpy.FieldMap()
            fm_soil = arcpy.FieldMap()
            fm_landuse = arcpy.FieldMap()
            fms = arcpy.FieldMappings()

            fm_parcels.addInputField(inParcels_inmemory,field_parcel_ID)
            fm_soil.addInputField(inSoil,field_soil_type)
            fm_landuse.addInputField(inLandUse,field_land_use)

            fms.addFieldMap(fm_parcels)
            fms.addFieldMap(fm_soil)
            fms.addFieldMap(fm_landuse)

            #Intersect
            #Only 2 inputs allowed with Intersect with basic liscense, so intermediate step needed
            arcpy.Intersect_analysis([inParcels_inmemory,inLandUse],outTemp)
            arcpy.Intersect_analysis([outTemp,inSoil],outTemp2)

            #Intersect with flood debasement layer if selected
            if bool_use_flood == 'true' and flood_layer and flood_field:
                arcpy.Intersect_analysis([outTemp2,flood_layer],outTemp3)   #Won't work with overlapping debasement polygons
                arcpy.Union_analysis([outTemp2,outTemp3],outAllFields)          #Union adds areas not covered by debasement layer to output. These will default to 1

                fm_flood = arcpy.FieldMap() #Add flood debasement field to output
                fm_flood.addInputField(flood_layer,flood_field)
                fms.addFieldMap(fm_flood)
            else:
                arcpy.CopyFeatures_management(outTemp2,outAllFields)

            #Get rid of unwanted fields
            arcpy.FeatureClassToFeatureClass_conversion(outAllFields,"in_memory","Final",field_mapping=fms)

            #Test for overlap
            arcpy.Intersect_analysis(outFinal,outOverlap)  #Final output is intersected with itself. Only overlapping areas will be in outOverlap
            result = arcpy.GetCount_management(outOverlap)
            count = int(result.getOutput(0))
            if count != 0:
                arcpy.AddWarning('Result contains overlapping polygons. Make sure there is no overlap in input layers.')

            #Always include GIS acreage in shapefile output. It will only be used in TXT and CSV if neither GIS acreage nor Deeded acreage is selected
            arcpy.AddField_management(outFinal,field_gis_acreage_output,'Double')         #Area in acres will be stored here
            arcpy.CalculateField_management(outFinal,field_gis_acreage_output,'!SHAPE.area@ACRES!','PYTHON')

            #Calculate deeded acreage of result
            #Gets ratio of Deeded Acreage to GIS Acreage for each parcel, then applies that ratio to each output feature with the same PIN
            if manual_acreage:    #OVERRIDES deeded acres field if manual acreage is given
                arcpy.AddMessage('Using manual acreage...')
                arcpy.AddField_management(outFinal,field_deeded_acreage_output,'Double')         #Area in acres will be stored here
                field_area = field_deeded_acreage_output

                cursor = arcpy.da.SearchCursor(inParcels_inmemory, [field_parcel_ID,'SHAPE@AREA'])
                area_ratio_dict = {}    #initialize empty dictionary
                for row in cursor:
                    if row[1] !=  0:    #check for divide by zero
                        area_ratio_dict[row[0]] = manual_acreage/row[1]
                    else:
                        area_ratio_dict[row[0]] = 0
                        arcpy.AddError('Area of parcel cannot be 0')
                        raise arcpy.ExecuteError    #stop execution
                cursor = arcpy.da.UpdateCursor(outFinal, [field_parcel_ID,field_deeded_acreage_output,'SHAPE@AREA'])
                for row in cursor:
                    row[1] = area_ratio_dict[row[0]] * row[2]       #result is in acres
                    cursor.updateRow(row)
            elif (bool_use_deeded == 'true' and field_deeded_acres):    #Deeded acreage field given in Settings tool
                arcpy.AddMessage('Using deeded acreage field...')
                arcpy.AddField_management(outFinal,field_deeded_acreage_output,'Double')         #Area in acres will be stored here
                field_area = field_deeded_acreage_output

                cursor = arcpy.da.SearchCursor(inParcels_inmemory, [field_parcel_ID,field_deeded_acres,'SHAPE@AREA'])
                area_ratio_dict = {}
                for row in cursor:
                    if row[1] is not None:  #checks if value has been entered in deeded acres field
                        area_ratio_dict[row[0]] = row[1]/row[2]     #acres/ft^2
                    else:
                        area_ratio_dict[row[0]] = .0000229568336506 #ft^2 to acres conversion factor for below. Gives GIS acreage if no deeded acreage is available.
                        arcpy.AddWarning('No Deeded Acreage given for {0}. Using GIS Acreage instead.'.format(row[0]))
                cursor = arcpy.da.UpdateCursor(outFinal, [field_parcel_ID,field_deeded_acreage_output,'SHAPE@AREA'])
                for row in cursor:
                    row[1] = area_ratio_dict[row[0]] * row[2]       #result is in acres
                    cursor.updateRow(row)
            else:   #Use GIS acreage
                arcpy.AddMessage('Using GIS acreage...')
                field_area = field_gis_acreage_output   #GIS acreage used for TXT and CSV outputs

            #Check whether flood debasement is being used
            if bool_use_flood == 'true' and flood_layer and flood_field:
                arcpy.AddMessage('Using flood debasement layer...')
                cursor = arcpy.da.UpdateCursor(outFinal, [flood_field])
                #Change multiplier of 0 or null to 1.
                for row in cursor:
                    if row[0] is None or row[0] == 0 or row[0] == '':  #check for null field
                        row[0] = 1.00
                    cursor.updateRow(row)

            #Write to CSV
            #Values for bool_csv and bool_txt are strings: 'true' and 'false', they are NOT bool values. This is because they are read from the config file.
            if bool_csv == 'true':
                arcpy.AddMessage('Writing to CSV...')
                try:
                    with open(outCSV, 'wb') as csvFile:
                        csvWriter = csv.writer(csvFile, delimiter=',',lineterminator='\r\n')
                        csvWriter.writerow(headings_csv[1::2])  #skip config file option names

                        cursor = arcpy.da.SearchCursor(outFinal, [field_parcel_ID,field_land_use,field_soil_type,field_area])
                        for row in cursor:
                            acres = round(row[3],2) #rounded to 2 decimal places
                            if acres == 0:
                                acres = 0.01    #Set bottom value at .01 acres
                            csvWriter.writerow([row[0], row[1], row[2], acres]) #changing the order of the headings will not change the order of the values
                except:
                        arcpy.AddError('CSV failed to write. Make sure CSV file is not open and file name is valid.')
                        self.PrintError()

            #Write to TXT
            if bool_txt == 'true':
                arcpy.AddMessage('Writing to TXT...')
                try:
                    textFile = open(outTXT,'w')

                    #Flood Debasement
                    if bool_use_flood == 'true' and flood_layer and flood_field:
                        cursor = arcpy.da.SearchCursor(outFinal, [field_parcel_ID,field_land_use,field_soil_type,field_area,flood_field])
                    else:
                        cursor = arcpy.da.SearchCursor(outFinal, [field_parcel_ID,field_land_use,field_soil_type,field_area])
                        flood_multiplier = '1.00'   #default debasement multiplier

                    for row in cursor:
                        #Acres
                        acres = round(row[3],2)
                        if acres == 0:
                            acres = 0.01    #Set bottom value at .01 acres

                        #Parcel ID
                        row0_string = str(row[0])       #makes translate work for string or number
                        Parcel_ID_number = row0_string.translate(None,string.punctuation)   #Remove punctuation from parcel ID. Works even if no punctuation exists.

                        #Soil Type
                        #Splits the soil type into two parts. The 1st is anything before the 1st non-digit character, and the 2nd is the 1st non-digit character(\D) and one digit(\d) after it if one exists(?).
                        soilType_split = re.split('(\D\d?)', str(row[2]))   #str() prevents numeric fields from giving an error
                        if len(soilType_split)==1:
                            soilType_split.append('A1')  #no second soil type, default is A1
                        elif soilType_split[1]=='W':
                            soilType_split[0]='W'   #move W to first column
                            soilType_split[1]=''
                        elif soilType_split[1].isalpha():
                            soilType_split[1]= soilType_split[1] + '1'  #if second part is only a letter, add 1 after it

                        #Land Use
                        value_land_use = row[1]
                        if value_land_use in land_use_codes:    #check if land use is in list of codes from config file
                            code_land_use = land_use_codes[land_use_codes.index(value_land_use)+1]  #Find value in list, then output code is next item
                        else:
                            code_land_use = land_use_codes[land_use_codes.index('DEFAULT')+1]   #use default code

                        #Flood Debasement
                        if bool_use_flood == 'true' and flood_layer and flood_field:    #needs to be checked again, or else row[4] will not exist
                            flood_multiplier = row[4]

                        textFile.write('{:<8} {:<8} {:<5} {:<15} {:<10} {:<8}'.format(soilType_split[0], soilType_split[1], code_land_use, Parcel_ID_number, acres, flood_multiplier))  #increase numbers to add more spaces for large values
                        textFile.write('\r\n')

                    textFile.close()
                except:
                    arcpy.AddError('TXT failed to write. Make sure TXT file is not open and file name is valid.')
                    self.PrintError()

            #Write result to shapefile if option is selected in Settings
            try:
                if bool_shapefile == 'true':
                    arcpy.AddMessage('Writing to shapefile...')
                    shapefile_path = os.path.join(outFolder, fileName + '.shp')
                    arcpy.CopyFeatures_management(outFinal,shapefile_path)

                    #Add shapefile to map as a layer
                    try:
                        mxd = arcpy.mapping.MapDocument("CURRENT")              #current mxd
                        df = arcpy.mapping.ListDataFrames(mxd,"*")[0]           #top data frame

                        #Check to see if shapefile layer already exists, if not add it to map
                        layer_list = arcpy.mapping.ListLayers(mxd,"",df)
                        shapefile_layer = arcpy.mapping.Layer(shapefile_path)
                        layer_names = []
                        for lyr in layer_list:
                            layer_names.append(lyr.name)
                        if not shapefile_layer.name in layer_names:
                            arcpy.mapping.AddLayer(df,shapefile_layer)
                    except:
                        arcpy.AddWarning('Shapefile could not be added to map. Please add manually.')
                        self.PrintError()
            except:
                arcpy.AddWarning('Shapfile failed to write.')
                self.PrintError()

            #Check if no outputs were selected
            if bool_csv == 'false' and bool_txt == 'false' and bool_shapefile == 'false':
                arcpy.AddWarning('No output type was selected, so no output files were written. Select at least one output type in Settings tool')

        except:
            self.PrintError()

        return

    #Reads config file to fill tool's parameters
    def ReadConfig(self, configfile_read, parameters):

        try:
            with open(configfile_read) as fp:
                config=ConfigParser.RawConfigParser(allow_no_value = False)
                config.optionxform = str    #Makes config file case sensitive. Do not change.
                config.readfp(fp)
        except:
            self.read_config_error = True   #this is checked in updateMessages()
            return

        #Get Parameters
        #if value is null or does not exist, nothing will be done and it will move on to the next parameter because everything is wrapped in a try statement
        #section and option are case sensitive
        try:
            parameters[self.p['PARCEL_LAYER']].value = config.get('LAYERS', 'Parcel')
        except: pass
        try:
            parameters[self.p['LANDUSE_LAYER']].value = config.get('LAYERS', 'LandUse')
        except: pass
        try:
            parameters[self.p['SOIL_LAYER']].value = config.get('LAYERS', 'SoilType')
        except: pass
        try:
            parameters[self.p['PARCEL_ID_FIELD']].value = config.get('FIELDS', 'ParcelID')
        except: pass
        try:
            parameters[self.p['LANDUSE_FIELD']].value = config.get('FIELDS', 'LandUse')
        except: pass
        try:
            parameters[self.p['SOIL_FIELD']].value = config.get('FIELDS', 'SoilType')
        except: pass
        try:
            parameters[self.p['OUTPUT_FOLDER']].value = config.get('OUTPUT', 'Folder')
        except: pass

    #Included whenever an exception is raised. Cannot only be included in final except statement
    def PrintError(self):
        # Return any Python specific errors and any error returned by the geoprocessor
        #
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n    " + \
                str(sys.exc_type)+ ": " + str(sys.exc_value) + "\n"
        arcpy.AddError(pymsg)

        msgs = "GP ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        arcpy.AddError(msgs)

class Settings(object):

    #p is a dictionary with class scope. The numbers are used as indexes for the parameters list. For example, parameters[self.p['OPEN_CONFIG']] is the same as parameters[0].
    #This was done to make modifying the parameters easier. If the order or number of parameters are changed, they need to be changed here AND in the getParameterInfo() method. getParameterInfo() initializes parameters, so it is separate from the other methods
    #0 should correspond to p0, 1 to p1, etc.
    p= {'OPEN_CONFIG':0,'PARCEL_LAYER':1, 'LANDUSE_LAYER':2,'SOIL_LAYER':3,'PARCEL_ID_FIELD':4,'LANDUSE_FIELD':5,'SOIL_FIELD':6,'BOOL_DEEDED':7,'DEEDED_FIELD':8,'BOOL_FLOOD':9,'FLOOD_LAYER':10,'FLOOD_FIELD':11,'OUTPUT_FOLDER':12,\
        'OUTPUT_CSV':13,'OUTPUT_TXT':14, 'OUTPUT_SHAPE':15, 'OVERWRITE_CONFIG':16,'SAVE_AS':17,'LANDUSE_CODES':18,'CSV_HEADINGS':19}
    read_config_error = False
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Settings"
        self.description = ""
        self.canRunInBackground = False

    #THIS METHOD ONLY RUNS THE FIRST TIME THE TOOL IS OPENED UNTIL ARCMAP IS RESTARTED. Initial parameters from the config file need to be determined in updateParameters() because it runs every time the tool is opened.
    #Otherwise, the settings tool will not affect OpenFarms until arcmap is restarted
    #To create new parameter: enter new p# and add it to params list at end of method. The order in the params list is the display order, except for categories, which are alphabetical. ALSO modify p dictionary above.
    def getParameterInfo(self):
        """Define parameter definitions"""

        p0 = arcpy.Parameter(
            displayName = 'Open Config File',
            name = 'config_read',
            datatype = 'DETextfile',
            parameterType = 'Optional',
            direction = 'Input')

        p1 = arcpy.Parameter(
            displayName = 'Input Parcel Layer',
            name = 'parcel_layer',
            datatype = 'GPFeatureLayer',
            parameterType = 'Required',
            direction = 'Input',
            category = '1 - Layers and Fields')

        p2 = arcpy.Parameter(
            displayName = 'Input Land Use Layer',
            name = 'landuse_layer',
            datatype = 'GPFeatureLayer',
            parameterType = 'Required',
            direction = 'Input',
            category = '1 - Layers and Fields')

        p3 = arcpy.Parameter(
            displayName = 'Input Soil Layer',
            name = 'soil_layer',
            datatype = 'GPFeatureLayer',
            parameterType = 'Required',
            direction = 'Input',
            category = '1 - Layers and Fields')

        p4 = arcpy.Parameter(
            displayName = 'Parcel ID Field',
            name = 'parcel_field',
            datatype = 'Field',
            parameterType = 'Required',
            direction = 'Input',
            category = '1 - Layers and Fields')
        p4.filter.list = ['Short','Long','Float','Single','Double','Text']
        p4.parameterDependencies = [p1.name]

        p5 = arcpy.Parameter(
            displayName = 'Land Use Field',
            name = 'landuse_field',
            datatype = 'Field',
            parameterType = 'Required',
            direction = 'Input',
            category = '1 - Layers and Fields')
        p5.filter.list = ['Short','Long','Float','Single','Double','Text']
        p5.parameterDependencies = [p2.name]

        p6 = arcpy.Parameter(
            displayName = 'Soil Type Field',
            name = 'soil_field',
            datatype = 'Field',
            parameterType = 'Required',
            direction = 'Input',
            category = '1 - Layers and Fields')
        p6.filter.list = ['Short','Long','Float','Single','Double','Text']
        p6.parameterDependencies = [p3.name]

        p7 = arcpy.Parameter(
            displayName = 'Use Deeded Acreage instead of GIS Acreage',
            name = 'bool_deeded',
            datatype = 'GPBoolean',
            parameterType = 'Optional',
            direction = 'Input',
            category = '1 - Layers and Fields')

        p8 = arcpy.Parameter(
            displayName = 'Deeded Acreage Field',
            name = 'deeded_field',
            datatype = 'Field',
            parameterType = 'Optional',
            direction = 'Input',
            category = '1 - Layers and Fields')
        p8.filter.list = ['Short','Long','Float','Single','Double']
        p8.parameterDependencies = [p1.name]
        p8.enabled = 0

        p9 = arcpy.Parameter(
            displayName = 'Use Flood Debasement Layer',
            name = 'bool_flood',
            datatype = 'GPBoolean',
            parameterType = 'Optional',
            direction = 'Input',
            category = '2 - Flood Debasement')

        p10 = arcpy.Parameter(
            displayName = 'Flood Debasement Layer',
            name = 'flood_layer',
            datatype = 'GPFeatureLayer',
            parameterType = 'Optional',
            direction = 'Input',
            category = '2 - Flood Debasement')
        p10.enabled = 0

        p11 = arcpy.Parameter(
            displayName = 'Flood Debasement Field',
            name = 'flood_field',
            datatype = 'Field',
            parameterType = 'Optional',
            direction = 'Input',
            category = '2 - Flood Debasement')
        p11.filter.list = ['Short','Long','Float','Single','Double']
        p11.parameterDependencies = [p10.name]
        p11.enabled = 0

        p12 = arcpy.Parameter(
            displayName = 'Output Folder',
            name = 'output_folder',
            datatype = 'DEFolder',
            parameterType = 'Optional',
            direction = 'Input',
            category = '3 - Output')

        p13 = arcpy.Parameter(
            displayName = 'Output .csv',
            name = 'output_csv',
            datatype = 'GPBoolean',
            parameterType = 'Optional',
            direction = 'Input',
            category = '3 - Output')
        p13.value = True

        p14 = arcpy.Parameter(
            displayName = 'Output .txt',
            name = 'output_txt',
            datatype = 'GPBoolean',
            parameterType = 'Optional',
            direction = 'Input',
            category = '3 - Output')

        p15 = arcpy.Parameter(
            displayName = 'Output Shapefile',
            name = 'output_shapefile',
            datatype = 'GPBoolean',
            parameterType = 'Optional',
            direction = 'Input',
            category = '3 - Output')

        p16 = arcpy.Parameter(
            displayName = 'Use Input Config (Overwrite)',
            name = 'overwrite_input_config',
            datatype = 'GPBoolean',
            parameterType = 'Optional',
            direction = 'Input',
            category = '4 - Save Config File')

        p17 = arcpy.Parameter(
            displayName = 'Save As',
            name = 'save_as',
            datatype = 'DETextfile',
            parameterType = 'Optional',
            direction = 'Output',
            category = '4 - Save Config File')

        #Multi value table
        p18 = arcpy.Parameter(
            displayName = 'Land Use Codes',
            name = 'landUseCodes',
            datatype = 'GPValueTable',
            parameterType = 'Optional',
            direction = 'Input',
            category ='5 - Land Use Codes')
        p18.columns = [['GPString', 'Land Use Field'],['GPString', 'Numeric Code for export']]  #[[Type,Name],[Type,Name]]

        #Multi value table
        p19 = arcpy.Parameter(
            displayName = 'CSV Headings',
            name = 'csv_headings',
            datatype = 'GPValueTable',
            parameterType = 'Optional',
            direction = 'Input',
            category = '6 - CSV Headings')
        p19.columns = [['GPString', 'Column'],['GPString', 'Heading']]

        try:    #does not work with 10.2
            p19.filters[0].type = 'ValueList'
            p19.filters[0].list = ['ParcelID','LandUse','SoilType','Acres'] #Only config file options are selectable. Otherwise, someone could create more than 4 headings, which will revert to default values in OpenFarms
        except: pass

        params = [p0,p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15,p16,p17,p18,p19]    #Don't forget to add parameters here!

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""

        return True

    #This method runs every time a parameter is updated. It also runs when the tool is opened. DO ALL INITIAL CONFIG FILE READING HERE, not in getParameterInfo().
    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        global configFile_old_Settings
        #This if statement will only be true when the tool is first opened, because OPEN_CONIFG is given a value inside it. Used for reading last used settings
        if (not parameters[self.p['OPEN_CONFIG']].value) and ( not parameters[self.p['OPEN_CONFIG']].altered):
            configFile_location = os.path.join(os.path.dirname(__file__),'config_location.txt')     #Contains location of last-used config only. Needs to be in same folder as this toolbox
            config=ConfigParser.RawConfigParser()
            config.optionxform = str        #Makes config file case sensitve. Do not remove
            config.read(configFile_location)

            parameters[self.p['OPEN_CONFIG']].value = config.get('DEFAULT','Location')  #Get location of last-used config file.

            if parameters[self.p['OPEN_CONFIG']].valueAsText is None:   #Should only be true the first time the tool is run. config_default.txt is located in same folder and packaged with add-in
                config_path = os.path.join(os.path.dirname(__file__),'config_default.txt')
                config=ConfigParser.RawConfigParser()
                config.optionxform = str
                config.set('DEFAULT','Location',config_path)
                with open(configFile_location, 'w') as configfile:
                    config.write(configfile)
                parameters[self.p['OPEN_CONFIG']].value = config_path

            configFile_old_Settings = parameters[self.p['OPEN_CONFIG']].valueAsText     #Remember current config file to decide if value changes later
            self.ReadConfig(parameters[self.p['OPEN_CONFIG']].valueAsText,parameters)   #Method that reads the config file, defined below. Different for each class.

        #Read config file if user has changed OPEN_CONFIG parameter. Altered property does not help because it remains true after being changed once
        if configFile_old_Settings != parameters[self.p['OPEN_CONFIG']].valueAsText:
           self.ReadConfig(parameters[self.p['OPEN_CONFIG']].valueAsText,parameters)
           configFile_old_Settings = parameters[self.p['OPEN_CONFIG']].valueAsText

        ##Enable certain parameters only when boolean parameters are checked
        #Deeded Acreage
        if parameters[self.p['BOOL_DEEDED']].value == True:
            parameters[self.p['DEEDED_FIELD']].enabled = 1
        else:
            parameters[self.p['DEEDED_FIELD']].enabled = 0

        #Flood Debasement
        if parameters[self.p['BOOL_FLOOD']].value == True:
            parameters[self.p['FLOOD_LAYER']].enabled = 1
            parameters[self.p['FLOOD_FIELD']].enabled = 1
        else:
            parameters[self.p['FLOOD_LAYER']].enabled = 0
            parameters[self.p['FLOOD_FIELD']].enabled = 0

        #Overwrite vs Save As: only allows one to be selected at a time. Overwriting an input parameter will cause an error, so it switches to the overwrite checkbox
        if parameters[self.p['SAVE_AS']].valueAsText == parameters[self.p['OPEN_CONFIG']].valueAsText:    #prevent same input and output
            parameters[self.p['OVERWRITE_CONFIG']].value = True
        if parameters[self.p['OVERWRITE_CONFIG']].value == True:
            parameters[self.p['SAVE_AS']].value = ''
            parameters[self.p['SAVE_AS']].enabled = 0
        else:
            parameters[self.p['SAVE_AS']].enabled = 1
        if parameters[self.p['SAVE_AS']].value:
            parameters[self.p['OVERWRITE_CONFIG']].value = False
            parameters[self.p['OVERWRITE_CONFIG']].enabled = 0
        else:
            parameters[self.p['OVERWRITE_CONFIG']].enabled = 1

        return

    #Runs after updateParameters(). Any warnings or errors could conflict with internal errors, which probably take precedence. All messages must be written here.
    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        arcpy.env.overwriteOutput = True    #prevents error message if overwriting existing file

        if self.read_config_error:  #set in ReadConfig() if exception is raised in opening the config file
            parameters[self.p['OPEN_CONFIG']].setWarningMessage('Config file did not load or could not be found. Choose another file or create a new one using settings.')

        if parameters[self.p['BOOL_DEEDED']].value == True and not parameters[self.p['DEEDED_FIELD']].value:    #Required/optional attribute is read-only. This is a substitute
            parameters[self.p['DEEDED_FIELD']].setWarningMessage('Deeded Acreage field is needed, or else GIS Acreage will be used.')
        else:
            parameters[self.p['DEEDED_FIELD']].clearMessage()

        if parameters[self.p['BOOL_FLOOD']].value == True and not parameters[self.p['FLOOD_LAYER']].value:
            parameters[self.p['FLOOD_LAYER']].setWarningMessage('Flood Debasement Layer is required')
        else:
            parameters[self.p['FLOOD_LAYER']].clearMessage()

        if parameters[self.p['BOOL_FLOOD']].value == True and not parameters[self.p['FLOOD_FIELD']].value:
            parameters[self.p['FLOOD_FIELD']].setWarningMessage('Flood Debasement Field is required')
        else:
            parameters[self.p['FLOOD_FIELD']].clearMessage()

        #Warns if neither save config option is selected
        if not parameters[self.p['OVERWRITE_CONFIG']].value and not parameters[self.p['SAVE_AS']].value:
            parameters[self.p['OVERWRITE_CONFIG']].setWarningMessage('No save option is currently selected. One save option must be selected.')
            parameters[self.p['SAVE_AS']].setWarningMessage('No save option is currently selected. One save option must be selected.')

        return

    #Runs after you press OK in the tool dialog
    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            overwrite_config = parameters[self.p['OVERWRITE_CONFIG']].valueAsText
            saveas_config = parameters[self.p['SAVE_AS']].valueAsText
            config_location = os.path.join(os.path.dirname(__file__),'config_location.txt') #stores path of main config file, located in same folder as this toolbox

            #Choose which config file to write to
            if overwrite_config == 'true':
                configFile_write = parameters[self.p['OPEN_CONFIG']].valueAsText
            elif saveas_config:
                configFile_write = saveas_config
            else:
                arcpy.AddError('No option selected for Save Config File. Settings will not be saved.')
                self.PrintError()
                raise arcpy.ExecuteError

            #Dictionary of lists. Used to easily organization information before writing to config file. Each key is a section of the config file. The lists are [option,value,option,value, etc.]
            param_dict = collections.OrderedDict()  #The keys will be in the same order they are initialized in (determines order in config file)
            param_dict['LAYERS'] = ['Parcel',parameters[self.p['PARCEL_LAYER']].valueAsText,'LandUse',parameters[self.p['LANDUSE_LAYER']].valueAsText,'SoilType',parameters[self.p['SOIL_LAYER']].valueAsText]
            param_dict['FIELDS'] = ['ParcelID',parameters[self.p['PARCEL_ID_FIELD']].valueAsText,'LandUse',parameters[self.p['LANDUSE_FIELD']].valueAsText,'SoilType',parameters[self.p['SOIL_FIELD']].valueAsText,'UseDeeded',parameters[self.p['BOOL_DEEDED']].valueAsText,'DeededAcres',parameters[self.p['DEEDED_FIELD']].valueAsText]
            param_dict['FLOOD_DEBASEMENT']  = ['UseFloodDebasement',parameters[self.p['BOOL_FLOOD']].valueAsText,'FloodDebasementLayer',parameters[self.p['FLOOD_LAYER']].valueAsText,'FloodDebasementField',parameters[self.p['FLOOD_FIELD']].valueAsText]
            param_dict['OUTPUT'] = ['Folder',parameters[self.p['OUTPUT_FOLDER']].valueAsText,'WriteCSV',parameters[self.p['OUTPUT_CSV']].valueAsText,'WriteTXT',parameters[self.p['OUTPUT_TXT']].valueAsText,'WriteShapefile',parameters[self.p['OUTPUT_SHAPE']].valueAsText]
            param_dict['SAVE']   = ['Overwrite',parameters[self.p['OVERWRITE_CONFIG']].valueAsText,'SaveAs',parameters[self.p['SAVE_AS']].valueAsText]
            param_dict['HEADINGS'] = list(itertools.chain(*parameters[self.p['CSV_HEADINGS']].value))   #results in same format as other lists in this dictionary
            param_dict['LANDUSE_CODES'] = list(itertools.chain(*parameters[self.p['LANDUSE_CODES']].value))

            #Write main config file
            config=ConfigParser.RawConfigParser()
            config.optionxform = str    #Make write case sensitive

            #Set config file text. Unfolds param_dict above.
            for section, item in param_dict.iteritems():
                config.add_section(section)
                for i in range(0,len(item),2):
                    if param_dict[section][i+1] is None:    #will be None if parameter is empty. If this is not included, the value will be read 'None' next time
                        param_dict[section][i+1] = ''
                    config.set(section,param_dict[section][i],param_dict[section][i+1])

            #Writes config file on disc
            try:
                with open(configFile_write, 'w') as configfile:
                    config.write(configfile)
                arcpy.AddMessage('Main config file saved.')
            except:
                arcpy.AddError('Main config file could not be saved.')
                self.PrintError()

            #Write location of config file (separate config_location.txt)
            config=ConfigParser.RawConfigParser()
            config.optionxform = str    #Make write case sensitive

            config.set('DEFAULT','Location',configFile_write)

            try:
                with open(config_location, 'w') as configfile:
                    config.write(configfile)
                arcpy.AddMessage('Config file location saved.')
            except:
                arcpy.AddError('Config file location could not be saved.')
                self.PrintError()
        except:
            self.PrintError()

        return

        #Reads config file to fill tool's parameters
    def ReadConfig(self, configfile_read, parameters):

        try:
            with open(configfile_read) as fp:
                config=ConfigParser.RawConfigParser(allow_no_value = False)
                config.optionxform = str    #Makes config file case sensitive. Do not change.
                config.readfp(fp)
        except:
            self.read_config_error = True    #checked in updateMessages()
            return

        #Get Parameters
        #if value is null or does not exist, nothing will be done and it will move on to the next parameter because everything is wrapped in a try statement
        #section and option are case sensitive
        try:
            parameters[self.p['PARCEL_LAYER']].value = config.get('LAYERS', 'Parcel')
        except: pass
        try:
            parameters[self.p['LANDUSE_LAYER']].value = config.get('LAYERS', 'LandUse')
        except: pass
        try:
            parameters[self.p['SOIL_LAYER']].value = config.get('LAYERS', 'SoilType')
        except: pass
        try:
            parameters[self.p['PARCEL_ID_FIELD']].value = config.get('FIELDS', 'ParcelID')
        except: pass
        try:
            parameters[self.p['LANDUSE_FIELD']].value = config.get('FIELDS', 'LandUse')
        except: pass
        try:
            parameters[self.p['SOIL_FIELD']].value = config.get('FIELDS', 'SoilType')
        except: pass
        try:
            parameters[self.p['BOOL_DEEDED']].value = config.get('FIELDS', 'UseDeeded')
        except: pass
        try:
            if config.get('FIELDS','DeededAcres') != None:
                parameters[self.p['DEEDED_FIELD']].value = config.get('FIELDS', 'DeededAcres')
        except: pass
        try:
            parameters[self.p['BOOL_FLOOD']].value = config.get('FLOOD_DEBASEMENT', 'UseFloodDebasement')
        except: pass
        try:
            if config.get('FLOOD_DEBASEMENT', 'FloodDebasementLayer') != None:
                parameters[self.p['FLOOD_LAYER']].value = config.get('FLOOD_DEBASEMENT', 'FloodDebasementLayer')
        except: pass
        try:
            if config.get('FLOOD_DEBASEMENT', 'FloodDebasementField') != None:
                parameters[self.p['FLOOD_FIELD']].value = config.get('FLOOD_DEBASEMENT', 'FloodDebasementField')
        except: pass
        try:
            parameters[self.p['OUTPUT_FOLDER']].value = config.get('OUTPUT', 'Folder')
        except: pass
        try:
            parameters[self.p['OUTPUT_CSV']].value = config.get('OUTPUT', 'WriteCSV')
        except: pass
        try:
            parameters[self.p['OUTPUT_TXT']].value = config.get('OUTPUT', 'WriteTXT')
        except: pass
        try:
            parameters[self.p['OUTPUT_SHAPE']].value = config.get('OUTPUT', 'WriteShapefile')
        except: pass
        try:
            parameters[self.p['OVERWRITE_CONFIG']].value = config.get('SAVE', 'Overwrite')
        except: pass
        try:
            if config.get('SAVE','SaveAs') != None:
                parameters[self.p['SAVE_AS']].value = config.get('SAVE','SaveAs')
        except: pass
        try:
            parameters[self.p['LANDUSE_CODES']].value = config.items('LANDUSE_CODES')
        except: pass
        try:
            parameters[self.p['CSV_HEADINGS']].value = config.items('HEADINGS')
        except: pass

    #Included whenever an exception is raised. Cannot only be included in final except statement
    def PrintError(self):
        # Return any Python specific errors and any error returned by the geoprocessor
        #
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n    " + \
                str(sys.exc_type)+ ": " + str(sys.exc_value) + "\n"
        arcpy.AddError(pymsg)

        msgs = "GP ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        arcpy.AddError(msgs)