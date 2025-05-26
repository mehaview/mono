import os

import ansys.fluent.core as pyfluent

from pathlib import Path  # isort:skip

if "__file__" not in locals():
    __file__ = Path(os.getcwd(), "mymesh.py")

output_file_name = 'mono'


# Data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "outputs")

###############################################################################
# Generate the mesh


def generate_mesh(
    output_file_name: str,
    data_dir: str,
    ui_mode: str | None = None,
):


    # Launch Fluent Meshing
    meshing = pyfluent.launch_fluent(
            precision="double",
            processor_count=4,
            mode="meshing",
            ui_mode=ui_mode,
            cwd=data_dir,
        )

    # Initialize workflow - m
    meshing.workflow.InitializeWorkflow(WorkflowType="Watertight Geometry")

    # Import the geometry
    geo_import = meshing.workflow.TaskObject["Import Geometry"]
    geo_import.Arguments.set_state(
        {
            "FileName": os.path.join(data_dir, f"{output_file_name}.pmdb"),
        }
    )
    geo_import.Execute()
    

    # Generate surface mesh
    surface_mesh_gen = meshing.workflow.TaskObject["Generate the Surface Mesh"]
    surface_mesh_gen.Arguments.set_state(
        {"CFDSurfaceMeshControls": {"MaxSize": 200, "MinSize": 0.2}}
    )
    surface_mesh_gen.Execute()
    

    # Describe the geometry
    describe_geo = meshing.workflow.TaskObject["Describe Geometry"]
    describe_geo.UpdateChildTasks(SetupTypeChanged=False)
    describe_geo.Arguments.set_state(
        {"SetupType": "The geometry consists of only fluid regions with no voids"}
    )
    describe_geo.UpdateChildTasks(SetupTypeChanged=True)
    describe_geo.Execute()

    # Update boundaries
    meshing.workflow.TaskObject["Update Boundaries"].Execute()

    # Update regions
    meshing.workflow.TaskObject["Update Regions"].Execute()

    # Add boundary layers
    add_boundary_layer = meshing.workflow.TaskObject["Add Boundary Layers"]
    add_boundary_layer.Arguments.set_state({"NumberOfLayers": 12})
    add_boundary_layer.AddChildAndUpdate()

    # Generate volume mesh
    volume_mesh_gen = meshing.workflow.TaskObject["Generate the Volume Mesh"]
    volume_mesh_gen.Arguments.set_state(
        {
            "VolumeFill": "poly-hexcore",
            "VolumeFillControls": {"HexMaxCellLength": 512},
            "VolumeMeshPreferences": {
                "CheckSelfProximity": "yes",
                "ShowVolumeMeshPreferences": True,
            },
        }
    )
    volume_mesh_gen.Execute()

    # Check mesh
    meshing.tui.mesh.check_mesh()

    # Write mesh
    meshing.tui.file.write_mesh(os.path.join(data_dir, f"{output_file_name}.msh.h5"))

    # Close Fluent Meshing
    meshing.exit()


###############################################################################
# Executing the mesh generation


generate_mesh(output_file_name, DATA_DIR)
