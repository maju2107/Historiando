"""Reference leg cage: evenly spaced rings, rounded feet, small side knee poles.

Input positions are in the final character frame (front -Y, height 3.6).
The existing hip boundary and perineal bridge are retained verbatim.
"""
import math


def rebuild_legs(verts, faces, regions, ns):
    old_names = [name for name in regions
                 if name.startswith(('Leg & foot.', 'Knee /'))]
    old_ids = {i for name in old_names for i in regions[name]}
    result = [f for f in faces if not old_ids.intersection(f)]
    for name in old_names:
        del regions[name]

    def vertex(co, name):
        i = len(verts)
        verts.append(tuple(co))
        regions.setdefault(name, []).append(i)
        return i

    # z, center X, radius X, center Y, radius Y, front instep lowering.
    # Reference knee is 0.76 above the sole, and the feet widen gradually.
    profiles = [
        (1.200, .169, .158, .013, .164, .000),
        (1.100, .186, .165, .009, .161, .000),
        (1.000, .204, .169, .006, .158, .000),
        (.905, .221, .173, .002, .156, .000),
        (.810, .231, .176, .000, .155, .000),
        (.760, .236, .179, .000, .157, .000),
        (.710, .241, .183, .002, .164, .000),
        (.605, .253, .194, .003, .181, .000),
        (.495, .265, .208, .002, .204, .000),
        (.385, .277, .220, -.015, .243, .025),
        (.285, .283, .237, -.053, .284, .050),
        (.185, .285, .249, -.093, .326, .035),
        (.085, .285, .249, -.099, .338, .012),
        (.028, .285, .240, -.096, .330, .002),
        (.008, .285, .221, -.092, .308, .000),
    ]
    # Correspond to the inherited hip boundary, with four front-facing edges.
    angles = [math.radians(a) for a in
              (-135, -108, -72, -43, 0, 43, 72, 108, 135, 156, 180, 204)]

    for side, label, hip in ((1, 'L', ns['right_hip']),
                             (-1, 'R', ns['left_hip'])):
        hip = list(hip)
        if side < 0:
            hip = [hip[(8-i) % 12] for i in range(12)]
        name = 'Leg & foot.' + label
        rings = []
        for z, cx, rx, cy, ry, lower in profiles:
            ring = []
            # A soft square cross section only at the toe; ellipse on the leg.
            toe = max(0., min(1., (.38-z)/.22))
            power = 1.0 - .28*toe
            for a in angles:
                ca, sa = math.cos(a), math.sin(a)
                xx = math.copysign(abs(ca)**power, ca)
                yy = math.copysign(abs(sa)**power, sa)
                zz = z-lower*max(0., -sa)**1.5
                ring.append(vertex((side*(cx+rx*xx), cy+ry*yy, zz), name))
            rings.append(ring)

        levels = [hip] + rings
        for row, (a, b) in enumerate(zip(levels, levels[1:])):
            for c in range(12):
                # A tiny redirect on either side of the knee replaces the
                # previous broad front patella island. These two pairs of
                # quads are reconnected below, without adding density.
                if row in (5, 6) and c in (3, 11):
                    continue
                d = (c+1) % 12
                result.append((a[c], a[d], b[d], b[c]))
        for c in (3, 11):
            # Reconnect the six-vertex perimeter of two vertically adjacent
            # quads along the other diagonal, making a small 3/5-pole pair.
            top, mid, bottom = levels[5], levels[6], levels[7]
            d = (c+1) % 12
            result.append((top[d], mid[d], bottom[d], bottom[c]))
            result.append((bottom[c], mid[c], top[c], top[d]))

        sole = rings[-1]
        center = vertex((side*.285, -.092, .008), name)
        for c in range(0, 12, 2):
            result.append((center, sole[c], sole[(c+1) % 12], sole[(c+2) % 12]))

    return result
