# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Lmn2QgisDialog
                                 A QGIS plugin
 Plugin allows for automatic project build needed for updating Forest Numerical Map and data management
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-11-26
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Adam Kurzawiński
        email                : adam.kurzawinski@katowice.lasy.gov.pl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

"""

import os
import subprocess
import platform
import time
import shutil
import csv
import sys
import uuid
from zipfile import ZipFile
from qgis.core import (QgsProject,QgsLayerTreeGroup, QgsVectorLayer, QgsRasterLayer, QgsLayerTreeGroup,
    QgsCoordinateReferenceSystem,
    QgsSettings, QgsUnitTypes,QgsLayerTreeLayer)
from PyQt5.QtGui import QColor
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets, QtGui
from PyQt5.QtWidgets import QFileDialog, QLineEdit, QMessageBox, QPushButton
from datetime import datetime

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'lmn_2_qgis_dialog_base.ui'))

class Lmn2QgisDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        """Constructor."""
        super(Lmn2QgisDialog, self).__init__(parent)

        self.setupUi(self)
        self.iface = iface

        # dialog elemets connections to functions
        self.pbVacuum.clicked.connect(self.on_pbVacuum_clicked)
        self.pbCancel.clicked.connect(self.on_pbCancel_clicked)
        self.pbBrowseUNL.clicked.connect(self.on_pbBrowseUNL_clicked)
        self.pbBrowseSLMN.clicked.connect(self.on_pbBrowseSLMN_clicked)
        self.pbBrowsePOCH.clicked.connect(self.on_pbBrowsePOCH_clicked)
        self.pbBrowseKSLMN.clicked.connect(self.on_pbBrowseKSLMN_clicked)
        self.pbLoad.clicked.connect(self.on_pbLoad_clicked)

        override = 0 # dev utility for recreating project structure

        if override == 1:
            self.create_layers_csv("C:/Users/adam.kurzawinski/Documents/011_Geomatyka/007_Skrypty/004_lmn2qgis/000_daneTestowe/Layer_info.csv")

        else:
            self.check_if_project_open()

    ###dialog functions group

    def initGui(self):
        self.action = QtWidgets.QAction("Open Dialog", self.iface.mainWindow())
        self.action.triggered.connect(self.showDialog)
        self.iface.addPluginToMenu("&My Plugin", self.action)

    def showDialog(self):
        self.dialog.show()  # Show the dialog

    # utility to quickly open desired directory either on Win, Mac or Linux

    ### utility functions group

    def open_folder(self, folder_path):
        # Normalize the folder path and make sure it is absolute
        folder_path = os.path.abspath(folder_path)

        try:
            if sys.platform.startswith('win'):  # Windows
                subprocess.Popen(f'explorer "{folder_path}"')
            elif sys.platform == 'darwin':  # MacOS
                subprocess.Popen(['open', folder_path])
            else:  # Linux or other
                subprocess.Popen(['xdg-open', folder_path])
        except Exception as e:
            # Log the error or display a message
            print(f"Error opening folder: {e}")

    def unload(self):
        if self.dialog:
            self.dialog.close()  # Close the dialog if it's open
            self.dialog = None  # Clear the reference

    # utility for unzipping files
    # args:
    # file : provide fileName with full directory
    # dir  : provide directory where file should be unzipped
    def unzip(self, file, dir):
        with ZipFile(file, 'r') as zip:
            zip.extractall(dir)

    ###Plugin init functions

    # at plugin start checks if there is any project with unsaved changes open.
    # if yes it will bring up a dialog and ask user if he wants to save project
    # if yes proceeds to save_project
    # if no continues to project_creation_wizard
    def check_if_project_open(self): # ta funkcja musi być częśćiej uruchamiana przy ponownym uruchomieniu wtyczki!
        if QgsProject.instance().isDirty() or QgsProject.instance().fileName() != "":

            msg_box = QtWidgets.QMessageBox()
            msg_box.setWindowTitle("Wykryto niezapisane zmiany")
            msg_box.setText("Wykryto nie zapisane zmiany, czy chcesz zapisać obecny projekt? Nie zapisanie projektu może skutkować utratą danych.")

            tak_zapisz_button = msg_box.addButton("Tak zapisz", QtWidgets.QMessageBox.AcceptRole)
            nie_zapisuj_button = msg_box.addButton("Nie zapisuj", QtWidgets.QMessageBox.RejectRole)

            msg_box.setDefaultButton(nie_zapisuj_button)
            msg_box.exec()

            if msg_box.clickedButton() == tak_zapisz_button:
                self.save_project(QgsProject.instance())
            else:
                self.project_creation_wizard()

        else:
            self.project_creation_wizard()

    def save_project(self, project):
        if project.fileName():
            project.write()
            print(f"Project saved at: {project.fileName()}")
        else:
            options = QtWidgets.QFileDialog.Options()

            # Prompt user to select a file to save the project

            file_name, _ = QtWidgets.QFileDialog.getSaveFileName(
                None,
                "Save Project",
                "",
                "QGIS Project Files (*.qgz *.qgs);;All Files (*)",
                options=options
            )

            if file_name:  # If the user selected a file
                project.write(file_name)  # Save the project to the selected file
                print(f"Project saved at: {file_name}")

            else:
                self.check_if_project_open()

    ### Project builder functions

    # prompts user if he wants to build new project from scratch
    # if no exits plugin
    # if yes builds new project
    def project_creation_wizard(self):
        # Step 1: Prompt user
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Tworzenie nowego projektu")
        msg_box.setText(
            "Czy chcesz utworzyć nowy projekt? Wybranie 'Nie' zakończy działanie wtyczki."
        )

        tak_button = msg_box.addButton("Tak", QMessageBox.AcceptRole)
        nie_button = msg_box.addButton("Nie", QMessageBox.RejectRole)

        msg_box.setDefaultButton(nie_button)
        msg_box.exec()

        if msg_box.clickedButton() == tak_button:
            # Prompt user to select directory for the new project
            directory = QFileDialog.getExistingDirectory(self.iface.mainWindow(), "Select Directory")

            if not directory:
                return  # User canceled the dialog

            # Step 2: Generate a unique project name and check for uniqueness
            current_date = datetime.now().strftime("%d-%m-%Y")
            project_directory = None
            unique_id = None
            max_attempts = 5
            attempt = 0

            # Loop to ensure the generated directory name is unique, retry up to max_attempts
            while attempt < max_attempts:
                unique_id = str(uuid.uuid4())[:4]  # Generate a 4-character unique ID
                project_directory = os.path.join(directory, f"Aktualizacja_{current_date}_{unique_id}")

                # Check if the directory already exists
                if not os.path.exists(project_directory):
                    break  # If directory doesn't exist, exit the loop

                attempt += 1  # Increment the attempt counter

            # If after max_attempts a unique name was not found, stop the plugin and show an error message
            if attempt == max_attempts:
                QMessageBox.critical(
                    self.iface.mainWindow(),
                    "Błąd",
                    "Nie udało się wygenerować unikatowej nazwy projektu. Spróbuj zapisać projekt w innej lokalizacji, a jeśli problem się powtórzy zgłoś problem autorowi wtyczki"
                )
                return  # Exit the function to stop the plugin

            # Create new project directory if unique name was found
            os.makedirs(project_directory, exist_ok=True)

            # Step 3: Create new QGIS project file
            project_name = f"Aktualizacja_{current_date}_{unique_id}.qgz"
            project_path = os.path.join(project_directory, project_name)

            # Create an empty QGIS project
            QgsProject.instance().write(project_path)

            # Step 4: Create empty subdirectories within the new project directory
            subdirectories = ["001_UNL", "002_SLMN", "003_POCH", "004_KontroleSLMN"]

            for subdir in subdirectories:
                os.makedirs(os.path.join(project_directory, subdir), exist_ok=True)

            project = QgsProject.instance()

            # Set default CRS to EPSG 2180
            crs = QgsCoordinateReferenceSystem("EPSG:2180")
            project.setCrs(crs)

            # Set selection color to #ffff00 with 50% opacity
            selection_color = QColor("#ffff00")  # Yellow color
            selection_color.setAlpha(128)  # 50% opacity (0-255 scale)
            project.setSelectionColor(selection_color)

            # Set units for distance measurements to Meters
            project.setDistanceUnits(QgsUnitTypes.DistanceMeters)

            # Set units for area measurements to Hectares
            project.setAreaUnits(QgsUnitTypes.AreaHectares)  # 4 corresponds to hectares

            # Save the project
            project.write()

            # Notify the user of success
            QMessageBox.information(
                self.iface.mainWindow(),
                "Sukces",
                f"Utworzono projekt o nazwie {project_name} w folderze {project_directory}"
            )

            self.open_folder(project_directory)

            self.load_layers_from_csv(os.path.join(os.path.dirname(__file__), 'config', 'layer_references.csv'))

        else:
            self.unload()

    def load_layers_from_csv(self, csv_file_path):
        """Load layer definitions from a CSV file and organize them into corresponding groups"""
        project = QgsProject.instance()  # Get the current QGIS project
        layers_added = []  # To keep track of the added layers

        # Define the order of the groups explicitly
        group_order = ["001_UNL", "002_SLMN", "003_POCH", "004_KontroleSLMN"]

        # Create the groups in the correct order (before entering the loop)
        group_dict = {}  # Dictionary to hold the group references
        root = project.layerTreeRoot()

        # Create groups first
        for group_code in group_order:
            group = QgsLayerTreeGroup(group_code)
            root.addChildNode(group)
            group_dict[group_code] = group

        # Open the CSV file and read the data
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            # Iterate through each row in the CSV file
            for row in reader:
                layer_name = row['name']
                layer_type = int(row['type'])
                crs = row['crs']
                geometry_type = int(row['geometry_type'])
                provider_type = row['provider_type']
                source = row['source']

                # Check if CRS is valid
                crs_obj = QgsCoordinateReferenceSystem(crs) if crs else None

                # Create an empty layer (without attempting to load data)
                layer = None
                if provider_type == 'memory':
                    # Handle memory layers (create an empty layer)
                    uri = "Point?crs=" + crs if crs else "Point"  # Example for creating an empty memory layer
                    layer = QgsVectorLayer(uri, layer_name, "memory")

                elif provider_type == 'ogr':
                    # Handle OGR provider (e.g., shapefiles) - create a placeholder for the layer
                    if source in group_dict:
                        # Construct an invalid URI that points to a missing shapefile
                        layer_path = os.path.join(project.fileName(), source, f"{layer_name}.shp")
                        uri = f"ogr:{layer_path}"
                        layer = QgsVectorLayer(uri, layer_name, "ogr")
                    else:
                        print(f"Unsupported group: {source} for layer {layer_name}")
                        continue

                elif provider_type == 'delimitedtext':
                    # Handle delimited text (CSV files) - create a placeholder for the layer
                    if source == "001_UNL":
                        layer_path = os.path.join(project.fileName(), source, "unl", f"{layer_name}.txt")
                        uri = f"delimitedtext:{layer_path}"
                        layer = QgsVectorLayer(uri, layer_name, "delimitedtext")

                        # Set delimiter for delimited text layers only
                        if layer.isValid():
                            layer.setDelimiter('|')
                    else:
                        print(f"Invalid group for delimited text layer: {source}")
                        continue
                else:
                    print(f"Unsupported provider type: {provider_type} for layer {layer_name}")
                    continue

                # Check if the layer is created successfully (even if it's empty or invalid)
                if layer:
                    # Set CRS if available
                    if crs_obj:
                        layer.setCrs(crs_obj)

                    # Get the corresponding group name for the layer
                    folder_code = source  # Get the folder code (group name)
                    if folder_code in group_dict:
                        # Add the layer reference (even though it's empty) to the corresponding group
                        group_dict[folder_code].addChildNode(QgsLayerTreeLayer(layer))

                    layers_added.append(layer_name)

                else:
                    print(f"Failed to load layer {layer_name} from {source}")

        # Provide feedback on which layers were added
        print(f"Layers added: {', '.join(layers_added)}")

    def project_styler(self,project_path):
        print(project_path)

    ### Data management functions

    def import_data(self):
        print("placeHolder")

    ### Dev utility functions

    def get_layer_info(self, layer):
        """Gather information about each layer and modify the source based on the folder name"""
        # Get the data source URI for the layer
        source_uri = layer.dataProvider().dataSourceUri() if layer.isValid() else None

        # Initialize the folder code as None (in case no match is found)
        folder_code = None

        # Check if the layer source exists and is a valid URI
        if source_uri:
            # Extract the folder name from the source path
            folder_name = os.path.basename(os.path.dirname(source_uri))

            # Assign the corresponding folder code based on folder name
            if "unl" in folder_name:
                folder_code = "001_UNL"
            elif "SLMN" in folder_name:
                folder_code = "002_SLMN"
            elif "Pochodne_stare" in folder_name:
                folder_code = "003_POCH"
            elif "Kontrola" in folder_name:
                folder_code = "004_KontroleSLMN"

        # Return the layer information along with the folder code as the source
        layer_info = {
            'name': layer.name(),
            'type': layer.type(),
            'crs': layer.crs().authid() if layer.crs() else None,
            'geometry_type': layer.geometryType(),
            'provider_type': layer.dataProvider().name(),
            'source': folder_code,  # Store the folder code instead of the full path
        }
        return layer_info

    def create_layers_csv(self, output_file):
        """Create CSV with layer information"""
        project = QgsProject.instance()  # Get the current QGIS project
        layers = project.mapLayers().values()  # Get all layers in the project

        # Ensure the output directory exists
        output_directory = os.path.dirname(output_file)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # Open the CSV file to write the data
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['name', 'type', 'crs', 'geometry_type', 'provider_type', 'source']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write the header
            writer.writeheader()

            # Iterate over layers in the project
            for layer in layers:
                # Get layer information
                layer_info = self.get_layer_info(layer)

                # Write the layer info to the CSV
                writer.writerow(layer_info)

        print(f"Layer information saved to {output_file}")