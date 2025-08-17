import numpy as np
from mathutils import Vector, Matrix, Euler
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon

class CollisionDetector:
    def __init__(self):
        pass
    
    def get_block_vertices(self, position, size, rotation):
        """
        Get the 8 vertices of a block given its position, size, and rotation.
        """
        l, w, h = size
        half_l = l / 2
        half_w = w / 2
        half_h = h / 2
        
        # Create rotation matrix from Euler angles
        rotation_matrix = Euler(rotation, 'XYZ').to_matrix().to_4x4()
        
        # 8 vertices in local space
        local_vertices = [
            Vector(( half_l,  half_w,  half_h)),
            Vector(( half_l,  half_w, -half_h)),
            Vector(( half_l, -half_w,  half_h)),
            Vector(( half_l, -half_w, -half_h)),
            Vector((-half_l,  half_w,  half_h)),
            Vector((-half_l,  half_w, -half_h)),
            Vector((-half_l, -half_w,  half_h)),
            Vector((-half_l, -half_w, -half_h))
        ]
        
        # apply rotation and translation to get world coordinates
        world_vertices = []
        for vertex in local_vertices:
            rotated_vertex = rotation_matrix @ vertex

            world_vertex = Vector(position) + rotated_vertex
            world_vertices.append(world_vertex)
        
        return world_vertices
    
    def get_block_faces(self, vertices):
        """
        Get the faces of a block given its vertices.
        Each face is represented by a list of vertices.
        """
        faces = [
            [0, 1, 3, 2],  
            [4, 5, 7, 6],  
            [0, 4, 6, 2],  
            [1, 5, 7, 3],  
            [0, 1, 5, 4],  
            [2, 3, 7, 6]   
        ]
        
        return [[vertices[i] for i in face] for face in faces]
    
    def separating_axis_theorem(self, vertices1, vertices2):
        """
        Check for collision between two sets of vertices using the Separating Axis Theorem (SAT).
        Returns True if there is a collision, False otherwise.
        """
        # get all possible separating axes
        normals = self.get_all_separating_axes(vertices1, vertices2)
        
        # check each axis
        for normal in normals:
            min1, max1 = self.project_vertices(vertices1, normal)
            min2, max2 = self.project_vertices(vertices2, normal)
            
            if max1 < min2 or max2 < min1:
                return False
        # If no separating axis found, there is a collision
        return True
    
    def get_all_separating_axes(self, vertices1, vertices2):
        """
        Get all possible separating axes for two sets of vertices.
        This includes face normals and edge cross products.
        """
        faces1 = self.get_block_faces(vertices1)
        normals1 = [self.get_face_normal(face) for face in faces1]
        
        faces2 = self.get_block_faces(vertices2)
        normals2 = [self.get_face_normal(face) for face in faces2]
        
        edge_normals = []
        for i in range(len(faces1)):
            for j in range(len(faces2)):
                edges1 = self.get_face_edges(faces1[i])
                edges2 = self.get_face_edges(faces2[j])
                
                for edge1 in edges1:
                    for edge2 in edges2:
                        cross = edge1.cross(edge2)
                        if cross.length > 0.001:  # To avoid zero-length normals
                            edge_normals.append(cross.normalized())
        
        all_normals = normals1 + normals2 + edge_normals
        
        unique_normals = []
        seen = set()
        for normal in all_normals:
            # Round to avoid floating point precision issues
            key = (round(normal.x, 3), round(normal.y, 3), round(normal.z, 3))
            if key not in seen:
                seen.add(key)
                unique_normals.append(normal)
        
        return unique_normals
    
    def get_face_normal(self, face_vertices):
        """
        Calculate the normal vector of a face given its vertices.
        The face is defined by three vertices.
        """
        v0 = face_vertices[0]
        v1 = face_vertices[1]
        v2 = face_vertices[2]
        
        edge1 = v1 - v0
        edge2 = v2 - v0
        
        normal = edge1.cross(edge2).normalized()
        return normal
    
    def get_face_edges(self, face_vertices):
        """
        Get the edges of a face defined by its vertices.
        Each edge is represented as a vector from one vertex to the next.
        """
        edges = []
        n = len(face_vertices)
        for i in range(n):
            j = (i + 1) % n
            edge = face_vertices[j] - face_vertices[i]
            edges.append(edge)
        return edges
    
    def project_vertices(self, vertices, axis):
        """
        Project the vertices onto a given axis and return the min and max values.
        The axis should be a normalized vector.
        """
        min_val = float('inf')
        max_val = float('-inf')
        
        for vertex in vertices:
            projection = vertex.dot(axis)
            
            if projection < min_val:
                min_val = projection
            if projection > max_val:
                max_val = projection
        
        return min_val, max_val
    
    def check_block_collision(self, scene, new_position, new_size, new_rotation):
        """
        Check if a new block collides with existing blocks in the scene.
        """
        new_vertices = self.get_block_vertices(new_position, new_size, new_rotation)
        
        for block in scene.blocks:
            if not block.blender_object:
                continue
                
            existing_vertices = self.get_block_vertices(
                block.position, 
                block.size, 
                block.rotation
            )
            
            if self.separating_axis_theorem(new_vertices, existing_vertices):
                return True  
        
        return False  