import arcpy
import pythonaddins
import os

class OpenFarms(object):
    """Implementation for OpenFarms_addin.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        toolbox = os.path.join(os.path.dirname(__file__), 'Toolbox_OpenFarms.pyt')
        pythonaddins.GPToolDialog(toolbox,'OpenFarms')

class Settings(object):
    """Implementation for Settings_addin.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        toolbox = os.path.join(os.path.dirname(__file__), 'Toolbox_OpenFarms.pyt')
        pythonaddins.GPToolDialog(toolbox,'Settings')