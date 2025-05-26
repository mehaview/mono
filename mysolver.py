

import os

import ansys.fluent.core as pyfluent
import numpy as np

from pathlib import Path 

if "__file__" not in locals():
    __file__ = Path(os.getcwd(), "wf_gmf_03_fluent_solver.py")
# sphinx_gallery_end_ignore

output_file_name = 'mono'


# Data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "outputs")

# Simulation parameters

def extract_value(file_content, setting):
    for line in file_content.splitlines():
        if line.startswith(setting):
            return int(line.split('=')[1].strip())
    return None

# Open the settings.txt file and read its content
with open('settings.txt', 'r') as file:
    file_content = file.read()

# Extract the values of angle and speed
angle1 = extract_value(file_content, 'angle')
l = extract_value(file_content, 'BOX_SIZE_LENGTH')
w = extract_value(file_content, 'BOX_SIZE_WIDTH')
h = extract_value(file_content, 'BOX_SIZE_HEIGHT')

surfaces = ["plate"]

angle = 90+angle1
radians = np.radians(angle)

SIM_MACH = 0.0437  # 0.8395 # Mach number >> 15m/s
SIM_TEMPERATURE = 290  # In Kelvin = 16 celsius
SIM_AOA = 0  # in degrees
SIM_PRESSURE = 101325 #Pascals, this is approximately equal to the pressure in Earth's atmosphere.

def solve_flow(
    sim_mach: float,# 0.0437 = 15m/s 
    sim_temperature: float,# 16 degree
    sim_aoa: float, 
    sim_pressure: float,
    data_dir: str,
    iter_count: int = 1,
    ui_mode: str | None = None,
):


    # Switch to Fluent solver
    solver = pyfluent.launch_fluent(
            precision="double",
            processor_count=2,
            mode="solver",
            ui_mode=ui_mode,
            cwd=data_dir,
            start_timeout=500,
        )

    # Load mesh
    solver.file.read_mesh(file_name=f"{data_dir}/{output_file_name}.msh.h5")

    # Verify the mesh
    solver.mesh.check()


    viscous = solver.setup.models.viscous
    #viscous.model = "k-omega"
    viscous.model = "spalart-allmaras"
    #viscous.k_omega_model = "sst"
    viscous.spalart_allmaras_production = "vorticity-based"

    solver.setup.boundary_conditions.set_zone_type(
        zone_list=["inlet-fluid"], new_type="velocity-inlet"
    )

    inlet_fluid = solver.setup.boundary_conditions.velocity_inlet["inlet-fluid"]
    aoa = np.deg2rad(sim_aoa)
    inlet_fluid.momentum.velocity_specification_method = 'Magnitude and Direction'
    inlet_fluid.momentum.velocity = 15
    #inlet_fluid.momentum.gauge_pressure = 0



    reference_values = solver.setup.reference_values

    reference_values.compute(from_zone_name="inlet-fluid", from_zone_type="velocity-inlet")


    # Set the reference area
    reference_values.area = (w+h)*2*l
    #reference_values.area = 100
    # Set the reference density
    reference_values.density = 1.225
    reference_values.enthalpy = 0
    reference_values.velocity = 15
    # Set the reference zone
    reference_values.zone = "zone55092ced-f6fe-47b7-99d3-dbcd74f08565-fluid"

    #session.solution.report_definitions.force["drag-force1"] = {}
    solver.solution.report_definitions.force['drag-force1'] = {"zones" : surfaces, "force_vector" : [1, 0, 0]}

    solver.parameters.output_parameters.report_definitions["drag-force1"] = {
        "report_definition": "drag-force1"
    }

    # Set up a report plot to monitor the drag force
    solver.solution.monitor.report_plots["drag-force1"] = {
        "report_defs": ["drag-force1"],
        "print": True  # Print the drag force to the console
    }

    report_file_path = "E:/expirement/results/"+ str(angle1)+".txt"
    solver.settings.solution.monitor.report_files.create(name="drag-force1")
    solver.settings.solution.monitor.report_files["drag-force1"] = {
    "report_defs": ["drag-force1", "drag-force1"],
    "file_name": str(report_file_path),
    }



    # Initialize flow field
    solver.solution.initialization.hybrid_initialize()

    # Save case file
    solver.file.write(
        file_name=f"{data_dir}/{output_file_name}_initialization.cas.h5",
        file_type="case",
    )

    # Solve for requested iterations
    solver.solution.run_calculation.iterate(iter_count=iter_count)
    solver.file.write(
        file_name=f"{data_dir}/{output_file_name}_resolved.cas.h5",
        file_type="case",
    )
    # Write data file as well
    solver.file.write(
        file_name=f"{data_dir}/{output_file_name}_resolved.dat.h5",
        file_type="data",
    )

    # Exit Fluent
    solver.exit()



solve_flow(SIM_MACH, SIM_TEMPERATURE, SIM_AOA, SIM_PRESSURE, DATA_DIR)
