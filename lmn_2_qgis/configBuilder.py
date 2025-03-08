import os
import csv
from qgis.core import (QgsProject,QgsLayerTreeGroup, QgsVectorLayer, QgsRasterLayer, QgsLayerTreeGroup,
    QgsCoordinateReferenceSystem,
    QgsSettings, QgsUnitTypes)

### Dev functions

 # WARNING! For this code to work layers needs to be organized into groups as follows:
 # 001_UNL  -> Layers should be text type (.txt)
 # 002_SLMN -> Layers should be SHP type
 # 003_POCH ->  Layers should be SHP type
 # 004_KontroleSLMN ->  Layers should be SHP type
 # Otherwise it will return error. Structure should not be tampered with. Only txt and shp files are supported

def get_layer_info(layer):
    """Gather information about each layer based on folder name set the data source so layers can be read in built project"""
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


def create_layers_csv(output_file):
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
            layer_info = get_layer_info(layer)

            # Write the layer info to the CSV
            writer.writerow(layer_info)

    print(f"Layer information saved to {output_file}")


create_layers_csv("C:/Users/adam.kurzawinski/Documents/011_Geomatyka/007_Skrypty/004_lmn2qgis/000_daneTestowe/Layer_info_test.csv")