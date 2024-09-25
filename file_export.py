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
import mathutils
from pathlib import Path


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
    use_setting: EnumProperty(
        name="Export:",
        description="Select export option",
        items=(
            ('SCENE', "Entire scene", "Export all objects in the scene"),
            ('SELECTED', "Selected", "Export only selected objects in the scene"),
        ),
        default='SCENE',
    )
    
    test: BoolProperty(
        name="UVs",
        description="Export UVs for mesh",
        default=True
    )
    
    
    def execute(self, context):
        return self.export_scene(context, self.filepath, self.use_setting)
    
    
    def export_scene(self, context, filepath, use_some_setting):
        print(f"Exporting scene to {filepath}...")
        
        to_json = { "Name": Path(bpy.data.filepath).stem }
    
        with open(filepath, 'w', encoding='utf-8') as output:
            # Parse only root nodes
            json_objects = []
            for node in bpy.context.scene.objects:
                if node.parent is None:
                    json_objects.append(node.name + '.node')
                    self.export_node(node, filepath)
            to_json["Nodes"] = json_objects

            output.write(json.dumps(to_json, indent=4, sort_keys=True))
    
        return {'FINISHED'}

        
    def export_node(self, object, filepath):   
        node_name = object.name
        node_filepath = str(Path(filepath).parent) + '\\' + node_name + '.node'
        material_filename = node_name + '.mat'
        mesh_filename = node_name + '.mesh'
        
        # Write node data
        to_json = { "Name": node_name }
        
        # Parse transform matrix
        to_json["Transform"] = {
            "r0": f"{object.matrix_local[0][0]} {object.matrix_local[1][0]} {object.matrix_local[2][0]} {object.matrix_local[3][0]}",
            "r1": f"{object.matrix_local[0][1]} {object.matrix_local[1][1]} {object.matrix_local[2][1]} {object.matrix_local[3][1]}",
            "r2": f"{object.matrix_local[0][2]} {object.matrix_local[1][2]} {object.matrix_local[2][2]} {object.matrix_local[3][2]}",
            "r3": f"{object.matrix_local[0][3]} {object.matrix_local[1][3]} {object.matrix_local[2][3]} {object.matrix_local[3][3]}"
        }
            
        # Parse children objects
        json_objects = []
        for child in object.children:
            json_objects.append(child.name + '.node')
            self.export_node(child, filepath)
        to_json["Nodes"] = json_objects
            
        # Select object
        bpy.context.view_layer.objects.active = object
        
        if object.type == 'MESH':
            material_filepath = str(Path(filepath).parent) + '\\' + material_filename
            print(f"Exporting material to {material_filepath}...")
            to_json["Material"] = material_filename
            write_material_data(object, material_filepath)
            
            mesh_filepath = str(Path(filepath).parent) + '\\' + mesh_filename
            print(f"Exporting mesh to {mesh_filepath}...")
            to_json["Mesh"] = mesh_filename
            self.export_mesh(object, mesh_filepath)
        elif object.type == 'LIGHT':
            light_filepath = str(Path(filepath).parent) + '\\' + node_name + '.light'
            print(f"Exporting light source to {light_filepath}...")
            self.export_light(object, light_filepath)
            
        with open(node_filepath, 'w', encoding='utf-8') as output:
            output.write(json.dumps(to_json, indent=4, sort_keys=True))
            

    def export_mesh(self, object, filepath):
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
        
        # Get normals and tangents
        for polygon in mesh.polygons:
            for index in range(polygon.loop_start, polygon.loop_start + polygon.loop_total):
                if not exists(normals, mesh.loops[index].normal):
                    normals.append(mesh.loops[index].normal)
                    
                if not exists(tangents, mesh.loops[index].tangent):
                    tangents.append(mesh.loops[index].tangent)
        
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
    
    
    def export_material(self, object, filepath):
        mat = object.active_material
        
        to_json = {}
        
        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                for output in node.outputs:
                    if len(output.links) == 0:
                        continue
                    
                    link = output.links[0]
                    socket_name = link.to_socket.name
                    if socket_name == 'Base Color':
                        to_json['Albedo'] = node.image.name
                    if socket_name == 'Metallic':
                        to_json['Metallic'] = node.image.name
                            
            if node.type == 'NORMAL_MAP':
                for input in node.inputs:
                    for link in input.links:
                        if link.to_socket.name == 'Color':
                            to_json['Normal'] = link.from_socket.node.image.name
        
        
        with open(filepath, 'w', encoding='utf-8') as output:
            output.write(json.dumps(to_json, indent=4, sort_keys=True))
    
    
    def export_light(self, object, filepath):
        to_json = {
            'Color': f'{object.data.color[0]}, {object.data.color[1]}, {object.data.color[2]}',
            'Energy': object.data.energy
        }
        
        if object.data.type == 'POINT':
            to_json['Type'] = 'Point'
            to_json['Radius'] = object.data.cutoff_distance
        elif object.data.type == "SUN":
            to_json['Type'] = 'Directional'
            
        with open(filepath, 'w', encoding='utf-8') as output:
            output.write(json.dumps(to_json, indent=4, sort_keys=True))
    

# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(SceneExporter.bl_idname, text="Custom Scene Export (.scene)")


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
