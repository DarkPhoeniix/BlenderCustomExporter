bl_info = {
    'name': 'Blender Exporter',
    'version': (1, 1),
    'blender': (4, 2, 0),
    'location': 'File > Export',
    'description': 'Export Custom Scene',
    'category': 'Import-Export'}


import bpy
import bpy_extras
from bpy_extras.io_utils import ExportHelper
from bpy.props import *
from bpy.types import Operator
import json
import mathutils
from pathlib import Path
from math import radians


def console_log(message: str):
    '''Helper function to write a log to the Blender's console'''
    print(message)


class SceneExporter(Operator, ExportHelper):
    '''This appears in the tooltip of the operator and in the generated docs'''
    
    bl_idname = 'custom_export.scene'  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = 'Export Scene Data'
    
    # ExportHelper mix-in class uses this.
    filename_ext = '.scene'
    
    filter_glob: StringProperty(
        default='*.scene',
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
    
    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting: EnumProperty(
        name='Export:',
        description='Select export option',
        items=(
            ('SCENE', 'Entire scene', 'Export all objects in the scene'),
            ('SELECTED', 'Selected', 'Export only selected objects in the scene'),
        ),
        default='SCENE',
    )
    
    test: BoolProperty(
        name='UVs',
        description='Export UVs for mesh',
        default=True
    )
    
    
    def execute(self, context):
        '''Run export command with given context'''
        return self.export_scene(context, self.filepath, self.use_setting)
    
    
    def export_scene(self, context, filepath, use_some_setting):
        '''Exports all object of the scene to filepath'''

        console_log(f'Exporting scene to {filepath}...')
        
        to_json = {}
        to_json['Name'] = Path(bpy.data.filepath).stem  # Scene name
    
        # Export scene root nodes
        with open(filepath, 'w', encoding='utf-8') as output:
            json_objects = []
            for node in bpy.context.scene.objects:
                if node.parent is None:
                    json_objects.append(node.name + '.node')
                    self.export_node(node, filepath)
            to_json['Nodes'] = json_objects

            output.write(json.dumps(to_json, indent=4, sort_keys=True))
    
        return {'FINISHED'}

        
    def export_node(self, node, filepath):
        '''Exports the node to the given filepath. \n
        Parses mesh, material, animations and light components'''

        parent_path = str(Path(filepath).parent) + '\\'

        # Node datapath  
        node_name = node.name
        node_filepath = parent_path + node_name + '.node'

        # Material datapath  
        material_filename = node_name + '.mat'
        material_filepath = parent_path + material_filename

        # Mesh datapath  
        mesh_filename = node_name + '.mesh'
        mesh_filepath = parent_path + mesh_filename

        # Armature datapath  
        armature_filename = node_name + '.arm'
        armature_filepath = parent_path + armature_filename

        # Animation datapath  
        animation_filename = node_name + '.anim'
        animation_filepath = parent_path + animation_filename

        # Light datapath 
        light_filename = node_name + '.light'
        light_filepath = parent_path + light_filename
        

        # Parse transformation matrix and convert coord system
        transform_matrix = mathutils.Matrix.transposed(node.matrix_local)                     # Change right-handed system to left-handed
        transform_matrix[1], transform_matrix[2] = transform_matrix[2], transform_matrix[1]   # Change Z-up to Y-up axis
        
        # Parse children objects
        children_objects = []
        for child in node.children:
            if node.type == 'CAMERA':
                continue            
            children_objects.append(child.name + '.node')
            self.export_node(child, filepath)
        
        # Write node's data
        to_json = {}
        to_json['Name'] = node_name
        to_json['Transform'] = {
            'r0': f'{transform_matrix[0][0]} {transform_matrix[0][1]} {transform_matrix[0][2]} {transform_matrix[0][3]}',
            'r1': f'{transform_matrix[1][0]} {transform_matrix[1][1]} {transform_matrix[1][2]} {transform_matrix[1][3]}',
            'r2': f'{transform_matrix[2][0]} {transform_matrix[2][1]} {transform_matrix[2][2]} {transform_matrix[2][3]}',
            'r3': f'{transform_matrix[3][0]} {transform_matrix[3][1]} {transform_matrix[3][2]} {transform_matrix[3][3]}'
        }
        to_json['Children'] = children_objects

        # Parse data for specific types
        if node.type == 'MESH':
            to_json['Material'] = material_filename
            self.export_material(node, material_filepath)
            
            to_json['Mesh'] = mesh_filename
            self.export_mesh(node, mesh_filepath)
            
            to_json['Armature'] = armature_filepath
            self.export_armature(node, armature_filepath)
            
            to_json['Animation'] = animation_filepath
            self.export_animation(node, animation_filepath)
            
        elif node.type == 'LIGHT':
            to_json['Light'] = light_filepath
            self.export_light(node, light_filepath)

        else:
            return
        
        with open(node_filepath, 'w', encoding='utf-8') as output:
            output.write(json.dumps(to_json, indent=4))
            

    def export_mesh(self, object, filepath):
        '''Exports object's mesh to the filepath. \n
        Mesh data:
          - v - vertex object coordinates
          - gi - vertex group index
          - gw - vertex group weight
          - vt - vertex UV coordinates
          - vn - vertex normal
          - vtan - vertex tangent
          - f - polygon (v/vt/vn/vtan)'''

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
        
        console_log(f'Exporting mesh to {filepath}...')

        bpy.context.view_layer.objects.active = object
        # Triangulate mesh
        bpy.ops.object.modifier_add(type='TRIANGULATE')
        bpy.ops.object.modifier_apply(modifier='Triangulate')
        
        mesh = object.to_mesh()
        mesh.calc_tangents() # Generate tangents data
        
        vertices = [v for v in object.data.vertices.values()]
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
        
        ### Write data to file
        # v - vertex object coordinates
        # gi - vertex group index
        # gw - vertex group weight
        # vt - vertex UV coordinates
        # vn - vertex normal
        # vtan - vertex tangent
        # f - polygon 'v/vt/vn/vtan'
        with open(filepath, 'w') as file:
            for vert in vertices:
                file.write(f'v {vert.co.x} {vert.co.y} {vert.co.z}\n')
            
            for vertex in object.data.vertices:
                file.write('gi')
                for group in vertex.groups:
                    file.write(f' {group.group}')
                file.write('\n')
                
            for vertex in object.data.vertices:
                file.write('gw')
                for group in vertex.groups:
                    file.write(f' {group.weight}')
                file.write('\n')
                
            for uv in uvs:
                file.write(f'vt {uv[0]} {uv[1]}\n')
            
            for normal in normals:
                file.write(f'vn {normal[0]} {normal[1]} {normal[2]}\n')
            
            for tangent in tangents:
                file.write(f'vtan {tangent[0]} {tangent[1]} {tangent[2]}\n')
            
            for polygon in mesh.polygons:
                file.write(f'f ')
                for index in range(polygon.loop_start, polygon.loop_start + polygon.loop_total):
                    file.write(f'{mesh.loops[index].vertex_index}/{get_index(uvs, mesh.uv_layers.active.data[index].uv)}/{get_index(normals, mesh.loops[index].normal)}/{get_index(tangents, mesh.loops[index].tangent)} ')
                file.write('\n')
    
    
    def export_material(self, object, filepath):
        '''Exports material data to the given filepath. \n
        Material parameters: albedo, metalness, normal map, roughness'''

        console_log(f'Exporting material to {filepath}...')

        mat = object.active_material
        
        if not mat:
            return
        
        to_json = {
            'Albedo':"",
            'Metalness':"",
            'Roughness':"",
            'Normal':""
        }
        
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
                        to_json['Metalness'] = node.image.name
                    if socket_name == 'Roughness':
                        to_json['Roughness'] = node.image.name
                            
            if node.type == 'NORMAL_MAP':
                for input in node.inputs:
                    for link in input.links:
                        if link.to_socket.name == 'Color':
                            to_json['Normal'] = link.from_socket.node.image.name
        
        
        with open(filepath, 'w', encoding='utf-8') as output:
            output.write(json.dumps(to_json, indent=4))
    
    
    def export_light(self, object, filepath):
        '''Exports light data to the given filepath. \n
        Light data:
          - TBD...'''

        console_log(f'Exporting light to {filepath}...')

        to_json = {
            'Color': f'{object.data.color[0]}, {object.data.color[1]}, {object.data.color[2]}',
            'Energy': object.data.energy
        }
        
        if object.data.type == 'POINT':
            to_json['Type'] = 'PointLight'
            to_json['Radius'] = object.data.cutoff_distance
        elif object.data.type == 'SUN':
            to_json['Type'] = 'DirectionalLight'
            
        with open(filepath, 'w', encoding='utf-8') as output:
            output.write(json.dumps(to_json, indent=4))
            
            
    def export_armature(self, object, filepath):
        '''Exports armature data to the given filepath'''

        # Helper function to parse bone's data
        def parse_bone_data(armature, bone):
            bone_info = {}
            bone_info['Name'] = bone.name
            # Calculate the inverse (bind pose matrix)
            rest_matrix = bone.matrix_local
            offset_matrix = rest_matrix.inverted()
            bone_transform = mathutils.Matrix.transposed(offset_matrix)
            bone_info['Offset'] = {
                'r0': f'{bone_transform[0][0]} {bone_transform[0][1]} {bone_transform[0][2]} {bone_transform[0][3]}',
                'r1': f'{bone_transform[1][0]} {bone_transform[1][1]} {bone_transform[1][2]} {bone_transform[1][3]}',
                'r2': f'{bone_transform[2][0]} {bone_transform[2][1]} {bone_transform[2][2]} {bone_transform[2][3]}',
                'r3': f'{bone_transform[3][0]} {bone_transform[3][1]} {bone_transform[3][2]} {bone_transform[3][3]}'
            }
            bone_info['Children'] = []
            for child_bone in bone.children:
                bone_info['Children'].append(parse_bone_data(armature, child_bone))

            return bone_info


        console_log(f'Exporting armature to {filepath}...')

        armature_obj = None
        armature = None
        
        for mod in object.modifiers:
            if mod.name == 'Armature':
                armature_obj = mod.object
                armature = armature_obj.data
        
        if armature_obj == None:
            console_log(f'Armature for {object.name} not found')
            return
        
        to_json = {}
        to_json['Armature'] = []

        for bone in armature.bones:
            if bone.parent is None:
                to_json['Armature'].append(parse_bone_data(armature, bone))

        with open(filepath, 'w', encoding='utf-8') as output:
            output.write(json.dumps(to_json, indent=4))


    def export_animation(self, object, filepath):
        '''Exports animation data to the given filepath'''

        armature_obj = None
        armature = None
        
        for mod in object.modifiers:
            if mod.name == 'Armature':
                armature_obj = mod.object
                armature = armature_obj.data
        
        if armature_obj == None:
            console_log(f'Armature for {object.name} not found')
            return
        
        pose = armature_obj.pose
        action = armature_obj.animation_data.action

        animations = {}
        animations[action.name] = {}

        # Determine the frame range of the action
        frame_start = int(action.frame_range[0])
        frame_end = int(action.frame_range[1])

        for frame_index in range(frame_start, frame_end + 1):
            bpy.context.scene.frame_set(frame_index)

            animations[action.name][frame_index] = {}
            for bone in pose.bones:
                parent_bone = bone.parent
                local_matrix = None

                # Calculate the local matrix relative to the parent
                if parent_bone:
                    parent_matrix = parent_bone.matrix
                    local_matrix = parent_matrix.inverted() @ bone.matrix
                else:
                    # No parent, local matrix equals pose matrix
                    local_matrix = bone.matrix
                
                matrix = mathutils.Matrix.transposed(local_matrix)
                
                animations[action.name][frame_index][bone.name] = {
                    'r0': f'{matrix[0][0]} {matrix[0][1]} {matrix[0][2]} {matrix[0][3]}',
                    'r1': f'{matrix[1][0]} {matrix[1][1]} {matrix[1][2]} {matrix[1][3]}',
                    'r2': f'{matrix[2][0]} {matrix[2][1]} {matrix[2][2]} {matrix[2][3]}',
                    'r3': f'{matrix[3][0]} {matrix[3][1]} {matrix[3][2]} {matrix[3][3]}'
                }
        
        to_json = animations
        
        with open(filepath, 'w', encoding='utf-8') as output:
            output.write(json.dumps(to_json, indent=4))
            

# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(SceneExporter.bl_idname, text='Custom Scene Export (.scene)')


# Register and add to the 'file selector' menu (required to use F3 search 'Text Export Operator' for quick access).
def register():
    bpy.utils.register_class(SceneExporter)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(SceneExporter)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == '__main__':
    register()
    bpy.ops.custom_export.scene('INVOKE_DEFAULT')
