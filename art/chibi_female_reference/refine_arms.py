"""Shape the editable arm/hand cage into softly rounded chibi volumes.

Called after the body has been transformed into the reference proportions.
Only coordinates change: the wrist fans, finger webs and quad connectivity
are preserved.  The two sides are constructed from matching local indices.
"""
import math


def refine_arms(verts, faces, regions, ns):
    # The original eight-vertex sections had a taper and unevenly displaced
    # centers inherited from the lowered-arm base.  These measurements keep
    # the almost parallel upper/lower arm contours seen in the T-pose views.
    sections = (
        (.350, .120, .115),
        (.458, .117, .113),
        (.610, .114, .111),
        (.674, .113, .110),
        (.737, .112, .109),
        (.890, .110, .107),
        (1.033, .107, .104),
    )
    for side, label in ((1, 'L'), (-1, 'R')):
        arm = regions['Arm.' + label]
        for row, (cx, ry, rz) in enumerate(sections):
            for k, idx in enumerate(arm[row * 8:(row + 1) * 8]):
                a = (k - 1) * math.pi / 4
                verts[idx] = (side * cx, ry * math.sin(a),
                              2.015 - rz * math.cos(a))

        palm = regions['Hand / palm.' + label]
        for row in range(4):
            ring = palm[row * 16:(row + 1) * 16]
            points = [verts[i] for i in ring]
            cz = sum(p[2] for p in points) / 16
            ymax = max(abs(p[1]) for p in points)
            # Preserve the broad top-view outline, but replace the square
            # top/side corners with an elliptical transition in the cage.
            for k, idx in enumerate(ring):
                x, y, z = verts[idx]
                v = y / ymax if ymax else 0.0
                corner_round = math.sqrt(max(.20, 1.0 - (.84 * v) ** 2))
                z = cz + (z - cz) * corner_round
                # The first palm section blends from the round wrist; the
                # knuckle section keeps its original bowed finger roots.
                y *= (1.01, 1.015, 1.005, 1.0)[row]
                verts[idx] = (x, y, z)

        # Relax the short junction from wrist to palm and the thumb saddle.
        # Neighbor averaging is deliberately restricted to this transition:
        # the support loops and tips of the fingers must retain their shape.
        candidate = set(arm[-8:] + palm[:48])
        thumb = regions['Finger / thumb.' + label]
        candidate.update(thumb[:8])
        adjacency = {i: set() for i in candidate}
        for face in faces:
            for a, b in zip(face, face[1:] + face[:1]):
                if a in adjacency:
                    adjacency[a].add(b)
                if b in adjacency:
                    adjacency[b].add(a)
        for _ in range(2):
            old = list(verts)
            for idx, neighbors in adjacency.items():
                if not neighbors:
                    continue
                amount = .16 if idx in palm[:48] else .10
                mean = tuple(sum(old[j][axis] for j in neighbors) / len(neighbors)
                             for axis in range(3))
                verts[idx] = tuple(old[idx][axis] * (1 - amount) +
                                   mean[axis] * amount for axis in range(3))

    # Explicit coordinate symmetry avoids drift in the fan neighborhoods.
    for stem in ('Arm.', 'Hand / palm.', 'Hand / webs.',
                 'Finger / thumb.', 'Finger / index.',
                 'Finger / middle.', 'Finger / little.'):
        left, right = regions.get(stem + 'L', ()), regions.get(stem + 'R', ())
        if len(left) != len(right):
            raise ValueError('Asymmetric arm region: ' + stem)
        for li, ri in zip(left, right):
            a, b = verts[li], verts[ri]
            x, y, z = (a[0] - b[0]) * .5, (a[1] + b[1]) * .5, (a[2] + b[2]) * .5
            verts[li], verts[ri] = (x, y, z), (-x, y, z)
