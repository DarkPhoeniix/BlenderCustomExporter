# Custom Blender Exporter

Blender add-on for exporting scene to custom format (.scene).</br>
Example:
```
BlenderScene
    ⤷ Node_01
        ⤷ Material_01
        ⤷ Mesh_01
    ⤷ Node_08
        ⤷ Node_02
            ⤷ Material_02
            ⤷ Mesh_01
    ⤷ Node_03
        ⤷ Material_04
        ⤷ Mesh_04
        ⤷ Node_04
            ⤷ Material_10
            ⤷ Mesh_09
    ⤷ Node_00
        ⤷ Light_01
```

### Scene description
```
{
    "Name": "MySceneName"           // Mandatory. Scene name from .blend file
    "Nodes":                        // Mandatory. Root nodes of the scene
    {
        "Node1.node",
        "Node2.node"
    }
}
```

### Node description
Contains a description of the current object in the scene hierarchy. The file has links to material and mesh files if they exist. 
```
{
    "Type": "Object",               // Mandatory. Type of the node (Object, Light)
    "Name": "MySceneName",          // Mandatory. Node name from Blender
    "Nodes":                        // Mandatory. Children nodes of the current node
    {
        "Node1.node",
        "Node2.node"
    },
    "Transform": {                  // Mandatory. Local transformation matrix of the current node
        "r0": "1.0 0.0 0.0 0.0",
        "r1": "0.0 1.0 0.0 0.0",
        "r2": "0.0 0.0 1.0 0.0",
        "r3": "1.0 2.0 3.0 1.0"
    },
    "Material": "ThisNode.mat",     // Optional.  Filepath of the metarial desc for the current node
    "Mesh": "ThisNode.mesh",        // Optional.  Filepath of the mesh desc for the current node
    "Light": "ThisNode.light"       // Optional.  Filepath of the light desc for the current node
}
```

### Material description
The file contains the path to all textures used for mesh in the current node.
```
{
    "Albedo": "Model_albedo.dds",   // Optional. Albedo/Base color texture file path
    "Metallics": "Model_metal.dds", // Optional. Metallic texture file path
    "Normal": "Model_normal.dds",   // Optional. Normal map file path
}
```

### Mesh description
Modified OBJ file format, added tangents, and changed face format to `vertex/uv/normal/tangent`
```
{
    v 1.0 0.0 -2.0                  // Vertex
    v 1.0 0.5 -2.0
    ...
    vn 1.0 0.0 0.0                  // Normal
    vn -1.0 0.0 0.0
    ...
    vt 0.8 0.7                      // UV
    vt 0.8 0.8
    ...
    vtan 0.0 1.0 0.0                // Tangent
    vtan 0.0 -1.0 0.0
    ...
    f 0/1/0/2 1/2/1/4 2/5/3/7       // Face description: vertex/uv/normal/tangent
}
```

### Light description
File contains description of the light source.
```
{
    "Type": "Point",                // WIP
    "Color": "0.0, 20.0, -5.0",     // WIP
    "Energy": 150.0,                // WIP
    "Radius": 20.0,                 // WIP
}
```

</br>
</br>
</br>

### TODO List

- [x] Implement basic scene parsing 
- [x] Implement mesh parsing (modified OBJ format)
- [x] Implement material/texture parsing
- [ ] Add copying needed textures to the output folder
- [ ] Improve folder structure
- [ ] Add textures format converter to DDS (BC7) + MipMaps generation
- [ ] Add Camera node support
- [x] Add Light (Point, Directional) nodes support
- [ ] Improve material graph parsing algo
- [ ] Implement partial scene parsing (only selected objects)
