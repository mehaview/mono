import os
from pathlib import Path
from typing import List, Union

from ansys.geometry.core import launch_modeler
from ansys.geometry.core.connection import GEOMETRY_SERVICE_DOCKER_IMAGE, GeometryContainers
from ansys.geometry.core.math import Plane, Point2D, Point3D
from ansys.geometry.core.plotting import GeometryPlotter
from ansys.geometry.core.sketch import Sketch
import numpy as np


#
image = None
if "ANSYS_GEOMETRY_RELEASE" in os.environ:
    image_tag = os.environ["ANSYS_GEOMETRY_RELEASE"]
    for geom_services in GeometryContainers:
        if image_tag == f"{GEOMETRY_SERVICE_DOCKER_IMAGE}:{geom_services.value[2]}":
            print(f"Using {image_tag} image")
            image = geom_services
            break


if "__file__" not in locals():
    __file__ = Path(os.getcwd(), "design.py")

GRAPHICS_BOOL = False  



output_file_name = 'mono'



# Data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "outputs")

# sphinx_gallery_start_ignore
if "DOC_BUILD" in os.environ:
    GRAPHICS_BOOL = True
# sphinx_gallery_end_ignore

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
BOX_SIZE_LENGTH = extract_value(file_content, 'BOX_SIZE_LENGTH')
BOX_SIZE_WIDTH = extract_value(file_content, 'BOX_SIZE_WIDTH')
BOX_SIZE_HEIGHT = extract_value(file_content, 'BOX_SIZE_HEIGHT')
angle = 180-angle1
center_x = 0.0
center_y = 0.0
radius = 0.5
gap = 0.05 # the distance bwn cylinders
e = 0.025 # the gap between the plate and the cylinders

#angle = 180-45
def rotate_point(point: Point2D, angle: float) -> Point2D:
    radians = np.radians(angle)
    x_new = point.x.magnitude * np.cos(radians) - point.y.magnitude * np.sin(radians)
    y_new = point.x.magnitude * np.sin(radians) + point.y.magnitude * np.cos(radians)
    return Point2D([x_new, y_new]) 

def move_point(point: Point2D, angle: float, radius: float) -> Point2D:
    r = radius / 2
    radians = np.radians(angle)
    #x_new = point.x.magnitude + np.cos(radians) * np.cos(radians) * 2 * r
    x_new = point.x.magnitude + np.sin(radians)*np.cos(radians)*2*r
    #y_new = point.y.magnitude + np.cos(radians) * np.sin(radians) * 2 * r
    y_new = point.y.magnitude + np.sin(radians)*np.sin(radians)*2*r
    return Point2D([x_new, y_new])

def generate_upper_half_cylinder(radius: float, n_points: int , gap: float ) -> List[Point2D]:
   
    points = []
 
    # Generate points for the upper half of the cylinder
    for i in range(n_points):
        theta = i / (n_points - 1) * np.pi  # Angle from 0 to pi (half circle)
        x = radius * np.cos(theta)
        y = radius * np.sin(theta) + gap / 2  # Add gap to the upper half
        points.append(Point2D([x, y]))
 
    # Close the upper half of the cylinder
    points.append(Point2D([radius, gap / 2]))
    points.append(Point2D([-radius, gap / 2]))
 
    return points
 
def generate_lower_half_cylinder(radius: float, n_points: int , gap: float ) -> List[Point2D]:
   
    points = []
 
    # Generate points for the lower half of the cylinder
    for i in range(n_points):
        theta = i / (n_points - 1) * np.pi  # Angle from 0 to pi (half circle)
        x = radius * np.cos(theta)
        y = -radius * np.sin(theta) - gap / 2  # Subtract gap from the lower half
        points.append(Point2D([x, y]))
 
    # Close the lower half of the cylinder
    points.append(Point2D([radius, -gap / 2]))
    points.append(Point2D([-radius, -gap / 2]))
 
    return points
 
def generate_rectangle(center_x: float, center_y: float, length: float, width: float) -> List[Point2D]:
    
    half_length = length 
    half_width = width / 2
    points = [
        Point2D([center_x - half_length, center_y - half_width]),
        Point2D([center_x + half_length, center_y - half_width]),
        Point2D([center_x + half_length, center_y + half_width]),
        Point2D([center_x - half_length, center_y + half_width]),
        Point2D([center_x - half_length, center_y - half_width])  # Close the rectangle
    ]
 
    return points



# Instantiate the modeler
modeler = launch_modeler(image=image)
print(modeler)


# Create the design
design = modeler.create_design(f"{output_file_name}")

# Create a sketch
sketch = Sketch()
c2 = Sketch()
rc = Sketch()

# Generate the points 
upper_half_cylinder_points = generate_upper_half_cylinder(radius=radius, n_points=200, gap=gap)
lower_half_cylinder_points = generate_lower_half_cylinder(radius=radius, n_points=200, gap=gap)
rectangle_points = generate_rectangle(center_x=center_x, center_y=center_y, length=radius, width=gap - e)

upper_half_cylinder_points_rotated = [rotate_point(point, angle) for point in upper_half_cylinder_points]
lower_half_cylinder_points_rotated = [rotate_point(point, angle) for point in lower_half_cylinder_points]
rectangle_points_rotated = [rotate_point(point, angle) for point in rectangle_points]

rectangle_points_moved = [move_point(point, angle, radius) for point in rectangle_points_rotated]

points = upper_half_cylinder_points_rotated
points2 = lower_half_cylinder_points_rotated
points3 = rectangle_points_moved


# Create the segments 
for i in range(len(points) - 1):
    sketch.segment(points[i], points[i + 1])

# Close 
sketch.segment(points[-1], points[0])

# Plot 
if GRAPHICS_BOOL:
    sketch.plot()

###############################################################################

for i in range(len(points2) - 1):
    c2.segment(points2[i], points2[i + 1])

# Close 
c2.segment(points2[-1], points2[0])

# Plot 
if GRAPHICS_BOOL:
    c2.plot()

###############################################################################
''''''
for i in range(len(points3) - 1):
    rc.segment(points3[i], points3[i + 1])

# Close
rc.segment(points3[-1], points3[1])

# Plot
if GRAPHICS_BOOL:
    rc.plot()

###############################################################################

# Extrude 
cly1 = design.extrude_sketch("half1", sketch, 1) # Extrusion: The function takes the 2D sketch and extends it into the third dimension
cly2 = design.extrude_sketch("half2", c2, 1)
rec = design.extrude_sketch("plate", rc, 1)
# Plot the design
if GRAPHICS_BOOL:
    design.plot()

###############################################################################
# Create the fluid domain
# -----------------------
# 
# Create the sketch

fluid_sketch = Sketch(plane=Plane(origin=Point3D([0, 0, 0.5 - (BOX_SIZE_WIDTH / 2)])))
fluid_sketch.box(
    center=Point2D([0.5, 0]),
    height=BOX_SIZE_HEIGHT,
    width=BOX_SIZE_LENGTH,
)

# Extrude the fluid domain
fluid = design.extrude_sketch("Fluid", fluid_sketch, BOX_SIZE_WIDTH)

# Create named selections in the fluid domain - inlet, outlet, and surrounding faces

fluid_faces = fluid.faces
surrounding_faces = []
inlet_faces = []
outlet_faces = []
for face in fluid_faces:
    if face.normal().x == 1:
        outlet_faces.append(face)
    elif face.normal().x == -1:
        inlet_faces.append(face)
    else:
        surrounding_faces.append(face)

design.create_named_selection("Outlet Fluid", faces=outlet_faces)
design.create_named_selection("Inlet Fluid", faces=inlet_faces)
design.create_named_selection("Surrounding Faces", faces=surrounding_faces)
design.create_named_selection("half1", faces=cly1.faces)
design.create_named_selection("half2", faces=cly2.faces)
design.create_named_selection("plate", faces=rec.faces)
# Plot the design intelligently...
if GRAPHICS_BOOL:
    geom_plotter = GeometryPlotter()
    geom_plotter.plot(cly1, color="blue")
    geom_plotter.plot(cly2, color="red")
    geom_plotter.plot(rec, color="orange")
    geom_plotter.plot(fluid, color="green", opacity=0.25)
    geom_plotter.show()


# Save the design
file = design.export_to_pmdb(DATA_DIR)
print(f"Design saved to {file}")



# Close the server session.
modeler.close()
