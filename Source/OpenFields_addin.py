import arcpy
import pythonaddins
import os

class OpenFields(object):
    """Implementation for OpenFields_addin.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        toolbox = os.path.join(os.path.dirname(__file__), 'Toolbox_OpenFields.pyt')
        pythonaddins.GPToolDialog(toolbox,'OpenFields')

class Settings(object):
    """Implementation for Settings_addin.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        toolbox = os.path.join(os.path.dirname(__file__), 'Toolbox_OpenFields.pyt')
        pythonaddins.GPToolDialog(toolbox,'Settings')