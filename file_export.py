bl_info = {
    "name": "Blender Exporter",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "File > Export",
    "description": "Export Custom Scene",
    "category": "Import-Export"}


import bpy
import bpy_extras
from bpy_extras.io_utils import ExportHelper
from bpy.props import *
from bpy.types import Operator
import json
from pathlib import Path


def write_scene_data(context, filepath, use_some_setting):
    print(f"Exporting scene to {filepath}...")
    
    # Write scene data
    with open(filepath, 'w', encoding='utf-8') as output:
        to_json = { "Name": Path(bpy.data.filepath).stem }

        # Parse only root nodes
        json_objects = []
        for node in bpy.context.scene.objects:
            if node.parent is None:
                json_objects.append(node.name + '.node')
                write_node_data(node, filepath)
        to_json["Nodes"] = json_objects

        output.write(json.dumps(to_json, indent=4))
    
    return {'FINISHED'}


def write_node_data(object, filepath):   
    node_name = object.name
    material_filename = node_name + '.mat'
    mesh_filename = node_name + '.mesh'
    
    # Write node data
    node_filepath = str(Path(filepath).parent) + '\\' + node_name + '.node'
    print(f"Exporting node to {node_filepath}...")
    with open(node_filepath, 'w', encoding='utf-8') as output:
        to_json = { "Material": material_filename,
                    "Mesh": mesh_filename,
                    "Name": node_name }
        
        # Parse children objects
        json_objects = []
        for child in object.children:
            json_objects.append(child.name + '.node')
            write_node_data(child, filepath)
        to_json["Nodes"] = json_objects
            
        output.write(json.dumps(to_json, indent=4))
    
    # Select object
    bpy.context.view_layer.objects.active = object
    
    if object.type == 'MESH':
        mesh_filepath = str(Path(filepath).parent) + '\\' + mesh_filename
        print(f"Exporting mesh to {mesh_filepath}...")
        write_mesh_data(object, mesh_filepath)
        
        material_filepath = str(Path(filepath).parent) + '\\' + material_filename
        print(f"Exporting material to {mesh_filepath}...")
        write_material_data(object, material_filepath)


def write_mesh_data(object, filepath):
    def exists(arr, target):
        for elem in arr:
            if elem == target:
                return True
        return False
    
    def get_index(arr, target):
        for i in range(len(arr)):
            if arr[i] == target:
                return i
        return -1
    
    
    current_obj = bpy.context.active_object
    
    # Triangulate mesh
    print(f"Triangulating mesh...")
    bpy.ops.object.modifier_add(type='TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier="Triangulate")
    
    mesh = object.to_mesh()
    
    vertices = [v for v in current_obj.data.vertices.values()]
    normals = []
    tangents = []
    uvs = []
    
    # Get UVs
    for uv in mesh.uv_layers.active.data:
        if not exists(uvs, uv.uv):
            uvs.append(uv.uv)
    
    # Get normals
    for polygon in mesh.polygons:
        for index in range(polygon.loop_start, polygon.loop_start + polygon.loop_total):
            if not exists(normals, mesh.loops[index].normal):
                normals.append(mesh.loops[index].normal)
                
            if not exists(tangents, mesh.loops[index].tangent):
                tangents.append(mesh.loops[index].tangent)l
    
    # Write data to file
    with open(filepath, 'w') as file:
        for vert in vertices:
            file.write(f"v {vert.co.x} {vert.co.y} {vert.co.z}\n")
        
        for uv in uvs:
            file.write(f"vt {uv[0]} {uv[1]}\n")
        
        for normal in normals:
            file.write(f"vn {normal[0]} {normal[1]} {normal[2]}\n")
        
        for tangent in tangents:
            file.write(f"vtan {tangent[0]} {tangent[1]} {tangent[2]}\n")
        
        for polygon in mesh.polygons:
            file.write(f"f ")
            for index in range(polygon.loop_start, polygon.loop_start + polygon.loop_total):
                file.write(f"{mesh.loops[index].vertex_index}/{get_index(uvs, mesh.uv_layers.active.data[index].uv)}/{get_index(normals, mesh.loops[index].normal)}/{get_index(tangents, mesh.loops[index].tangent)} ")
            file.write("\n")


def write_material_data(object, filepath):
    return


class SceneExporter(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "custom_export.scene"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Scene Data"
    
    # ExportHelper mix-in class uses this.
    filename_ext = ".scene"
    
    filter_glob: StringProperty(
        default="*.scene",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
    
    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting: BoolProperty(
        name="Example Boolean",
        description="Example Tooltip",
        default=True,
    )
    
    type: EnumProperty(
        name="Example Enum",
        description="Choose between two items",
        items=(
            ('OPT_A', "First Option", "Description one"),
            ('OPT_B', "Second Option", "Description two"),
        ),
        default='OPT_A',
    )
    
    def execute(self, context):
        return write_scene_data(context, self.filepath, self.use_setting)


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportSomeData.bl_idname, text="Custom Scene Export (.scene)")


# Register and add to the "file selector" menu (required to use F3 search "Text Export Operator" for quick access).
def register():
    bpy.utils.register_class(SceneExporter)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(SceneExporter)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
    bpy.ops.custom_export.scene('INVOKE_DEFAULT')
