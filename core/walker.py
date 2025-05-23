from typing import List, Tuple, Iterator
from core.geodesy import geod_dist, geod_interp


def walk_path(
    points: List[Tuple[float, float]], step_m: float, loop: bool
) -> Iterator[Tuple[float, float]]:
    """Yield points every `step_m` metres along the polyline; include endpoints."""
    if loop:
        # reverse for ping-pong behavior
        points = points + points[-2::-1]

    carry = 0.0  # leftover from previous segment
    cur = points[0]
    yield cur  # always yield first point

    for nxt in points[1:]:
        seg_len = geod_dist(cur, nxt)
        if seg_len == 0:
            continue
        # initial offset on this segment
        dist_from_cur = step_m - carry
        while dist_from_cur < seg_len:
            fix = geod_interp(cur, nxt, dist_from_cur)
            yield fix
            dist_from_cur += step_m
        # compute new carry into next segment
        carry = seg_len - (dist_from_cur - step_m)
        cur = nxt

    yield points[-1]  # ensure final endpoint is emitted
