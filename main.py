import eel
import os
from os import listdir
import subprocess
import sys
import json

from output_capture.output_capture import *
from cli_format.cli_visualizer import *
from cli_format.cli_reformat import *

opti_visualizer = None
data_visualizer = None

executor = ThreadPoolExecutor(max_workers=2)

futures = {}
progress = {}
materials = {}

   
def persistent_path(rel_path):
    if getattr(sys, 'frozen', False):
        # The application is frozen (PyInstaller)
        exe_dir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(exe_dir, rel_path)

def get_persistent_output_dir():
    output_dir = persistent_path("output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir
    
def get_data_dir():
    data_dir = persistent_path("data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

def get_data_output_dict():
    data_output_dict_path = persistent_path("dictionary.json")
    data_output_dict = {}
    if not os.path.exists(data_output_dict_path):
        with open("dictionary.json", "w") as file:
            pass
    else:
        with open(data_output_dict_path, 'r') as f:
            data_output_dict = json.load(f)
    return data_output_dict

OUTPUT_DIR = get_persistent_output_dir()
DATA_DIR = get_data_dir()
DATA_OUTPUT_DICT = get_data_output_dict()

materials_path = ""
terminal_output = []
default_materials = {
    "titanium_alloy": {
        "name": "Titanium Alloy",
        "kt": 7.0,
        "rho": 4420,
        "cp": 560,
        "vs": 0.6,
        "h": 20,
        "P": 150
    },
    "aluminum_alloy": {
        "name": "Aluminum Alloy",
        "kt": 120.0,
        "rho": 2700,
        "cp": 900,
        "vs": 1.0,
        "h": 20,
        "P": 250
    },
    "nickel_alloy": {
        "name": "Nickel Alloy",
        "kt": 12.0,
        "rho": 8190,
        "cp": 435,
        "vs": 0.8,
        "h": 20,
        "P": 300
    },
    "stainless_steel": {
        "name": "Stainless Steel",
        "kt": 22.5,
        "rho": 7990,
        "cp": 500,
        "vs": 0.6,
        "h": 50,
        "P": 100
    },
    "cobalt_chromium": {
        "name": "Cobalt Chromium",
        "kt": 14.0,
        "rho": 8300,
        "cp": 420,
        "vs": 0.7,
        "h": 20,
        "P": 200
    }
}


def resource_path(rel_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rel_path)

# eel.browsers.set_path('electron', resource_path('electron\electron.exe'))
eel.init('web', allowed_extensions=['.js', '.html'])


def store_custom_material(material_key, custom_material):
    try:
        global materials_path
        # Validate input
        if not isinstance(custom_material, dict) or "name" not in custom_material:
            raise ValueError("Invalid custom material format")
        materials[material_key] = custom_material
        
        with open(materials_path, 'w') as f:
            f.write(json.dumps(materials))
            
        return True

    except (IOError, json.JSONDecodeError) as e:
        print(f"Error saving custom material: {e}")
        return False
    
@eel.expose
def get_terminal_output():
    return terminal_output

@eel.expose
def get_materials():
    global materials
    global materials_path
    materials_path = persistent_path('materials.json')
    try:
        with open(materials_path, 'r') as f:
            materials = json.load(f)
        return materials
    except FileNotFoundError:
        with open(materials_path, 'w') as f:
            f.write(json.dumps(default_materials))
        return get_materials()
        
@eel.expose
def convert_cli_file(filecontent, filename, selected_material):
    display_status("Starting...")
    global OUTPUT_DIR
    global DATA_DIR
    if type(selected_material) == str:
        selected_material = json.loads(selected_material)
    
    display_status("Saving Custom Material...")
    material_key = "_".join(selected_material["name"].lower().strip().split(" "))
    if (material_key not in materials):
        store_custom_material(material_key, selected_material)
    
    # store original file
    data_file = os.path.join(DATA_DIR, filename)
    with open(data_file, "w") as f:
        f.write(filecontent)
    
    outputname = f"{filename}-{datetime.now().strftime('%m-%d-%Y_%H-%M-%S')}.cli"
    DATA_OUTPUT_DICT[outputname] = filename
        
    future = executor.submit(convertDYNCliFile, filecontent, filename, outputname, OUTPUT_DIR, progress, selected_material)
    futures[filename] = future
    progress[filename] = 0
    return "Task started"

@eel.expose
def get_task_status(filename):
    if filename in futures:
        future = futures[filename]
        if future.done():
            try:
                result = future.result()
                return {"status": "completed", "result": result}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return {"status": "in_progress", "progress": progress[filename]}
    else:
        return {"status": "not_found"}
    
@eel.expose
def view_processed_files():
    try:
        global OUTPUT_DIR
        
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            
        files = [f for f in listdir(OUTPUT_DIR) if f.endswith('.cli')]
        
        files.sort(key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x)), reverse=True)
        
        return files
    except Exception as e:
        print(f"Error listing processed files: {e}")
        return []

@eel.expose
def plot_with_slider():
    return plot_with_slider()

@eel.expose
def open_file_location(filename):
    try:
        global OUTPUT_DIR
        
        file_path = os.path.join(OUTPUT_DIR, filename)
        subprocess.Popen(f'explorer /select,"{file_path}"')
        
    except Exception as e:
        print(f"Error opening file location: {e}")
        return []

@eel.expose
def read_cli(filename):
    global opti_visualizer  # Add global keyword
    global OUTPUT_DIR
    opti_visualizer = CLIVisualizer(filename)
    
    opti_visualizer.read_cli_file(OUTPUT_DIR)
    return

@eel.expose
def comapreCLI(filename):
    global data_visualizer
    global opti_visualizer  # Add global keyword
    global DATA_DIR
    global OUTPUT_DIR
    global DATA_OUTPUT_DICT
    
    original_file = DATA_OUTPUT_DICT[filename]
    data_visualizer = CLIVisualizer(original_file)
    opti_visualizer = CLIVisualizer(filename)
    
    data_visualizer.read_cli_file(DATA_DIR)
    opti_visualizer.read_cli_file(OUTPUT_DIR)
    return
            
@eel.expose
def retrieve_layers():
    global opti_visualizer
    if opti_visualizer is None:
        return []
    return opti_visualizer.layers

@eel.expose
def get_num_layers():
    global opti_visualizer
    if opti_visualizer is None:
        return 0
    return opti_visualizer.get_num_layers()

@eel.expose
def get_num_hatches():
    global opti_visualizer
    if opti_visualizer is None:
        return 0
    return opti_visualizer.get_num_hatches()

@eel.expose
def get_r_from_layer():
    global opti_visualizer
    if opti_visualizer is None:
        return []
    return opti_visualizer.get_r_from_layer()

@eel.expose
def set_current_layer(layer_num):
    global opti_visualizer
    if opti_visualizer is not None:
        opti_visualizer.set_current_layer(layer_num)

@eel.expose
def set_current_hatch(hatch_num):
    global opti_visualizer
    if opti_visualizer is not None:
        opti_visualizer.set_current_hatch(hatch_num)
    
@eel.expose
def retrieve_bounding_box_from_layer():
    global opti_visualizer
    if opti_visualizer is None:
        return {'x': [], 'y': []}
    bounding_boxes = opti_visualizer.get_bounding_boxes_from_layer()
    return {'bounding_boxes': bounding_boxes, 'x_min': opti_visualizer.x_min, 'x_max': opti_visualizer.x_max, 'y_min': opti_visualizer.y_min, 'y_max': opti_visualizer.y_max}

@eel.expose
def retrieve_coords_from_cur():
    global opti_visualizer
    if opti_visualizer is None:
        return []
    coords = opti_visualizer.retrieve_hatch_lines_from_layer()
    return {'x': coords[0], 'y': coords[1], 'x_min': opti_visualizer.x_min, 'x_max': opti_visualizer.x_max, 'y_min': opti_visualizer.y_min, 'y_max': opti_visualizer.y_max}

output_capture = OutputCapture()
output_capture.start_capture()
eel.start('templates/app.html', mode="electron")
