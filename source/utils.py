from math import pi, sqrt, atan2, cos, sin


def analyze_key_tuple_str(key_tuple_str: str) -> tuple:
    key_tuple_str = key_tuple_str[1:-1]
    names = tuple(key_tuple_str.split(','))
    return names


def pos_to_hint(pos: list, ref) -> dict:
    hx = (pos[0]-ref.x)/ref.width
    hy = (pos[1]-ref.y)/ref.height
    return {'x': hx, 'y': hy}


def hint_to_pos(hint: dict, ref) -> list:
    hx = hint['x']
    hy = hint['y']
    pos = [hx*ref.width+ref.x, hy*ref.height+ref.y]
    return pos


def infer_points(start: list, end: list) -> list:
    alpha = pi/3
    d = sqrt((start[0]-end[0])**2+(start[1]-end[1])**2)
    r = 50
    points = start + end
    ang = atan2((start[1]-end[1])/d, (start[0]-end[0])/d)
    degrees = [ang+(alpha/2), ang-(alpha/2)]
    for degree in degrees:
        points.extend([end[0]+cos(degree)*r, end[1]+sin(degree)*r])
    points.extend(end)
    points = [int(point) for point in points]
    return points


def key_tuple_to_str(key_tuple: tuple) -> str:
    key_str = str(key_tuple)
    key_str = key_str.replace(' ', '')
    key_str = key_str.replace('\'', '')
    return key_str