import bpy
import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(project_root)
from bpy.props import (
    PointerProperty,
    CollectionProperty,
    IntProperty,
    FloatVectorProperty,
    StringProperty,
)
import bmesh
from bpy.types import PropertyGroup as BasePropertyGroup
from mathutils import Vector, Euler
from configs.constants import COLORS, MATERIALS

"""Class for a block."""
class Block(BasePropertyGroup):
    index: IntProperty()
    color: StringProperty()
    material_type: StringProperty()
    size: FloatVectorProperty()
    position: FloatVectorProperty(default=(0.0, 0.0, 0.0))
    rotation: FloatVectorProperty(default=(0.0, 0.0, 0.0))

    blender_object: PointerProperty(type=bpy.types.Object)
    
    def generate_a_block(self, scene):
        if self.blender_object:
            bpy.data.objects.remove(self.blender_object, do_unlink=True)
        
        mesh = self.create_mesh()
        obj = bpy.data.objects.new(f"Block_{self.index}", mesh)
        self.blender_object = obj

        self.apply_material(obj)
        self.apply_transfrom(obj)

        scene.collection.objects.link(obj)
        self.set_block_physics()
        return obj
    
    def create_mesh(self):
        size_str = f"{self.size[0]:.1f}x{self.size[1]:.1f}x{self.size[2]:.1f}"
        mesh_name = f"BlockMesh_{size_str}"

        if mesh_name in bpy.data.meshes:
            return bpy.data.meshes[mesh_name]
        
        L, W, H = self.size
        bm = bmesh.new()

        v1 = bm.verts.new((L/2, W/2, H))
        v2 = bm.verts.new((L/2, -W/2, H))
        v3 = bm.verts.new((-L/2, -W/2, H))
        v4 = bm.verts.new((-L/2, W/2, H))
        v5 = bm.verts.new((L/2, W/2, 0))
        v6 = bm.verts.new((L/2, -W/2, 0))
        v7 = bm.verts.new((-L/2, -W/2, 0))
        v8 = bm.verts.new((-L/2, W/2, 0))
        bm.faces.new((v1, v2, v3, v4))
        bm.faces.new((v8, v7, v6, v5)) 
        bm.faces.new((v1, v5, v6, v2))
        bm.faces.new((v3, v2, v6, v7))
        bm.faces.new((v4, v3, v7, v8))
        bm.faces.new((v4, v1, v8, v5))
        
        mesh = bpy.data.meshes.new(mesh_name)
        bm.to_mesh(mesh)
        bm.free()
        return mesh
    
    def apply_material(self, obj):
        mat_params = MATERIALS.get(self.material_type, {})

        base_mat_name = f"Material_{self.material_type}"
        base_material = bpy.data.materials.get(base_mat_name)
        if not base_material:
            base_material = bpy.data.materials.new(name=base_mat_name)
            base_material.use_nodes = True
            nodes = base_material.node_tree.nodes
            bsdf = nodes.get("Principled BSDF")

            for param, value in mat_params.items():
                if param in bsdf.inputs:
                    bsdf.inputs[param].default_value = value
            
            color = COLORS[self.color]
            color_name  = "_".join(f"{c:.1f}" for c in color)
            mat_name = f"{base_mat_name}_{color_name}"

            material = bpy.data.materials.get(mat_name)
            if not material:
                material = base_material.copy()
                material.name = mat_name

                bsdf = material.node_tree.nodes.get("Principled BSDF")
                bsdf.inputs['Base Color'].default_value = color

            if not obj.data.materials:
                obj.data.materials.append(material)
            else:
                obj.data.materials[0] = material

    def apply_transfrom(self, obj):
        obj.location = Vector(self.position)
        obj.rotation_euler = Euler(self.rotation, 'XYZ')
    
    def set_block_physics(self):
        """
        Set up the physics properties for the block.
        """
        bpy.context.view_layer.objects.active = self.blender_object
        bpy.ops.rigidbody.object_add()
        
        rb = self.blender_object.rigid_body
        rb.type = 'ACTIVE'
        rb.collision_shape = 'BOX'
        rb.mass = 1.0