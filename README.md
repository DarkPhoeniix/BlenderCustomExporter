# Custom Blender Exprter

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
Contains description of the current object in scene hierarchy. File has links to material and mesh files if they exist. 
```
{
    "Material": "Wyrm.mat",         // Optional. Filepath of the metarial desc for the current node
    "Mesh": "Wyrm.mesh",            // Optional. Filepath of the mesh desc for the current node
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
    }
}
```

### Material description
File contains filepath to all textures used for mesh in current node.
```
{
    "Albedo": "Model_albedo.dds",   // Optional. Albedo/Base color texture filepath
    "Metallics": "Model_metal.dds", // Optional. Metallic texture filepath
    "Normal": "Model_normal.dds",   // Optional. Normal map filepath
}
```

### Mesh description
Modified OBJ file format, added tangents and changed face format to `vertex/uv/normal/tangent`
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