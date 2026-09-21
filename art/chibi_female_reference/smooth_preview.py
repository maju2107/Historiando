"""Render the original control edges on the subdivided mesh.

This is a display helper, not retopology or mesh smoothing. The mesh modifiers
must do the actual smoothing. Catmull-Clark modifiers should use
``use_limit_surface=False``: the tracked paths then land on the same finite
subdivision vertices as Blender. Level 2 gives five points per control edge;
level 3 gives nine. Solidify is evaluated first, with only its outward copy of
each original edge displayed, so shell thickness does not misplace the wire.
"""

import bpy
from mathutils import Vector


_EDGE_ID = "_wire_original_edge"


def _edge_key(a, b):
    return (a, b) if a < b else (b, a)


def _subdivide(vertices, faces, chains, preserve_corners=False):
    """One Catmull-Clark step, carrying every input edge's ordered vertex path."""
    edges = {}
    vertex_edges = [[] for _ in vertices]
    vertex_faces = [[] for _ in vertices]
    face_centers = []
    for fi, face in enumerate(faces):
        center = sum((vertices[v] for v in face), Vector()) / len(face)
        face_centers.append(center)
        for v in face:
            vertex_faces[v].append(fi)
        for a, b in zip(face, face[1:] + face[:1]):
            key = _edge_key(a, b)
            if key not in edges:
                edges[key] = []
                vertex_edges[a].append(key)
                vertex_edges[b].append(key)
            edges[key].append(fi)

    updated = []
    for vi, point in enumerate(vertices):
        incident = vertex_edges[vi]
        boundary = [e[1] if e[0] == vi else e[0]
                    for e in incident if len(edges[e]) == 1]
        if boundary:
            if len(boundary) == 2 and not (preserve_corners and len(incident) == 2):
                updated.append(point * .75 + (vertices[boundary[0]] + vertices[boundary[1]]) * .125)
            else:
                updated.append(point.copy())
        elif incident:
            n = len(incident)
            fav = sum((face_centers[f] for f in vertex_faces[vi]), Vector()) / len(vertex_faces[vi])
            rav = sum(((vertices[a] + vertices[b]) * .5 for a, b in incident), Vector()) / n
            updated.append((fav + 2 * rav + (n - 3) * point) / n)
        else:
            updated.append(point.copy())

    edge_points = {}
    for (a, b), adjacent in edges.items():
        edge_points[a, b] = len(updated)
        if len(adjacent) == 2:
            updated.append((vertices[a] + vertices[b] + face_centers[adjacent[0]] + face_centers[adjacent[1]]) * .25)
        else:
            updated.append((vertices[a] + vertices[b]) * .5)
    face_start = len(updated)
    updated.extend(face_centers)
    new_faces = []
    for fi, face in enumerate(faces):
        for j, v in enumerate(face):
            new_faces.append([v, edge_points[_edge_key(v, face[(j + 1) % len(face)])],
                              face_start + fi, edge_points[_edge_key(face[j - 1], v)]])
    new_chains = []
    for chain in chains:
        traced = [chain[0]]
        for a, b in zip(chain, chain[1:]):
            traced.extend((edge_points[_edge_key(a, b)], b))
        new_chains.append(traced)
    return updated, new_faces, new_chains


def _pre_subdivision_mesh(obj):
    """Evaluate modifiers preceding subdivision, retaining original edge IDs."""
    original = obj.data
    original.update()
    normals = [v.normal.copy() for v in original.vertices]
    edge_data = {}
    for e in original.edges:
        a, b = e.vertices
        normal = (normals[a] + normals[b]).normalized()
        edge_data[e.index + 1] = ((original.vertices[a].co + original.vertices[b].co) * .5, normal)

    clone = obj.copy()
    clone.data = original.copy()
    clone.name = "_temporary_preview_source"
    bpy.context.scene.collection.objects.link(clone)
    attr = clone.data.attributes.get(_EDGE_ID)
    if attr is not None:
        clone.data.attributes.remove(attr)
    attr = clone.data.attributes.new(_EDGE_ID, 'INT', 'EDGE')
    for e in clone.data.edges:
        attr.data[e.index].value = e.index + 1

    levels = 0
    corners = False
    found_subdiv = False
    for mod in list(clone.modifiers):
        if mod.type == 'SUBSURF' and mod.show_render and not found_subdiv:
            levels = mod.render_levels
            corners = getattr(mod, 'boundary_smooth', 'ALL') == 'PRESERVE_CORNERS'
            found_subdiv = True
        if found_subdiv or not mod.show_render:
            clone.modifiers.remove(mod)
        else:
            mod.show_viewport = True

    try:
        bpy.context.view_layer.update()
        evaluated = clone.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh(preserve_all_data_layers=True,
                                 depsgraph=bpy.context.evaluated_depsgraph_get())
        vertices = [v.co.copy() for v in mesh.vertices]
        faces = [list(p.vertices) for p in mesh.polygons]
        ids = mesh.attributes.get(_EDGE_ID)
        if ids is None:
            raise RuntimeError("Pre-subdivision modifier discarded original edge IDs: " + obj.name)
        candidates = {}
        for e in mesh.edges:
            original_id = ids.data[e.index].value
            if original_id not in edge_data:
                continue  # new rim edges created by Solidify
            a, b = e.vertices
            mid, normal = edge_data[original_id]
            score = (((vertices[a] + vertices[b]) * .5) - mid).dot(normal)
            old = candidates.get(original_id)
            if old is None or score > old[0]:
                candidates[original_id] = (score, [a, b])
        chains = [candidates[i][1] for i in sorted(candidates)]
        evaluated.to_mesh_clear()
        return vertices, faces, chains, levels, corners
    finally:
        data = clone.data
        bpy.data.objects.remove(clone, do_unlink=True)
        bpy.data.meshes.remove(data)


def make_wire_overlay(parts, collection, material, bevel_depth=.0006):
    """Return a curve showing smooth paths of the original cage edges only.

    Supports ordinary Catmull-Clark control meshes and Solidify before Subsurf.
    Edge creases, Simple subdivision, and deformation after subdivision are not
    supported. No original mesh, modifier, or persistent selection is altered.
    """
    curves = bpy.data.curves.new('Arestas suaves da malha de controle', 'CURVE')
    curves.dimensions = '3D'
    curves.resolution_u = 1
    curves.bevel_depth = bevel_depth
    curves.bevel_resolution = 0
    edge_count = 0
    max_segments = 1
    for obj in parts:
        if obj.type != 'MESH':
            continue
        vertices, faces, chains, levels, corners = _pre_subdivision_mesh(obj)
        for _ in range(levels):
            vertices, faces, chains = _subdivide(vertices, faces, chains, corners)
        # Area-weighted surface normals avoid the old cage-normal offset error.
        normals = [Vector() for _ in vertices]
        for f in faces:
            center = sum((vertices[i] for i in f), Vector()) / len(f)
            normal = Vector()
            for a, b in zip(f, f[1:] + f[:1]):
                normal += (vertices[a] - center).cross(vertices[b] - center)
            for i in f:
                normals[i] += normal
        offset = bevel_depth * 1.15
        matrix = obj.matrix_world.copy()
        for chain in chains:
            spline = curves.splines.new('POLY')
            spline.points.add(len(chain) - 1)
            for point, vi in zip(spline.points, chain):
                co = matrix @ (vertices[vi] + normals[vi].normalized() * offset)
                point.co = (*co, 1)
        edge_count += len(chains)
        max_segments = max(max_segments, 2 ** levels)
    wire = bpy.data.objects.new('Topologia - apenas render', curves)
    collection.objects.link(wire)
    if material is not None:
        curves.materials.append(material)
    wire['display_only'] = True
    wire['original_edges'] = edge_count
    wire['max_segments_per_original_edge'] = max_segments
    wire['method'] = 'Original control edges tracked through Catmull-Clark; includes evaluated Solidify shell.'
    return wire
