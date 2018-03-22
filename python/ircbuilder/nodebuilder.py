import json
import math


def make_iter(i):
    try:
        return iter(i)
    except TypeError:
        return i,


def int_tuple(*args):
    my_list = []
    for arg in args:
        my_list.append(math.floor(float(arg) + 0.5))
    return tuple(my_list)


def build(x, y, z, item):
    """similar to MinetestConnection.set_node but stores nodes in node_dict rather than sending to minetest

    x, y, z: coordinates to be added to nodes. They are converted to integers so that each node has unique set of coordinates
    item: minetest item name as a string "default:glass", or json string '{"name":"default:torch", "param2":"1"}'
    x, y, z can also be supplied as iterables eg range or list or tuple or generator

    returns node_dict: {(x, y, z): item} Dictionary of node
    """
    if not isinstance(item, str):
        item = json.dumps(item)
    node_dict = {}
    for xi in make_iter(x):
        for yi in make_iter(y):
            for zi in make_iter(z):
                node_dict[int_tuple(xi, yi, zi)] = item
    return node_dict


def build_cuboid(x1, y1, z1, x2, y2, z2, item):
    """similar to MinetestConnection.set_nodes but stores nodes in node_dict rather than sending to minetest"""
    step_x = 1 if x2 > x1 else -1
    step_y = 1 if y2 > y1 else -1
    step_z = 1 if z2 > z1 else -1
    return build(range(x1, x2 + step_x, step_x), range(y1, y2 + step_y, step_y), range(z1, z2 + step_z, step_z), item)


def node_lists_with_cuboids(node_lists_flat):
    """Finds adjacent points in node_lists_flat and converts them to cuboids for data efficiency"""
    node_lists = {}
    for item, v in node_lists_flat.items():
        node_lists[item] = []
        # v is a list of singular tuples for given item
        # vs is sorted in ascending order
        vs = sorted(v)
        # look for consecutive blocks in x then y then z
        while len(vs) > 0:
            start_x, start_y, start_z = vs[0]
            dx, dy, dz = 0, 0, 0
            tfx, tfy, tfz = True, True, True
            while tfx or tfy or tfz:
                if tfx:
                    x = start_x+dx+1
                    for y in range(start_y, start_y+dy+1):
                        for z in range(start_z, start_z+dz+1):
                            if not (x, y, z) in vs:
                                tfx = False
                    if tfx:
                        dx += 1
                if tfy:
                    y = start_y+dy+1
                    for x in range(start_x, start_x+dx+1):
                        for z in range(start_z, start_z+dz+1):
                            if not (x, y, z) in vs:
                                tfy = False
                    if tfy:
                        dy += 1
                if tfz:
                    z = start_z+dz+1
                    for x in range(start_x, start_x+dx+1):
                        for y in range(start_y, start_y+dy+1):
                            if not (x, y, z) in vs:
                                tfz = False
                    if tfz:
                        dz += 1
            if dx == 0 and dy == 0 and dz == 0:
                node_lists[item].append((start_x, start_y, start_z))
            else:
                node_lists[item].append(((start_x, start_y, start_z), (start_x+dx, start_y+dy, start_z+dz)))
            for x in range(start_x, start_x+dx+1):
                for y in range(start_y, start_y+dy+1):
                    for z in range(start_z, start_z+dz+1):
                        vs.remove((x, y, z))
    return node_lists


def node_lists_from_node_dict(node_dict):
    """Convert node_dict to node_lists"""
    node_lists = {}
    for pos, item in node_dict.items():
        if item not in node_lists:
            node_lists[item] = []
        node_lists[item].append(pos)
    return node_lists_with_cuboids(node_lists)


def send_node_lists(mc, node_lists, end_list=()):
    """ Send node_lists to minetest. Should send air after walls so no lava and water flow in

    mc : MinetestConnection object
    node_lists : { 'item1':[(x1,y1,z1), ((x2a,y2a,z2a),(x2b,y2b,z2b)), ...], 'item2':[...]}
    end_list : ('air', 'door:')
    """
    item_list = list(node_lists.keys())
    # Convert end_list to iterable in the case only a string was provided
    try:
        end_list = iter(end_list)
    except TypeError:
        end_list = end_list,
    for item in end_list:
        for key in item_list:
            if key.find(item) == 0:
                item_list.remove(key)
                item_list.append(key)
    for item in item_list:
        mc.set_node_list(node_lists[item], item)


def send_node_dict(mc, node_dict, end_list=()):
    """Convert node_dict to node_lists and send to minetest

    mc : MinetestConnection object
    node_dict : { (x1,y1,z1):'item1', (x2,y2,z2):'item2', ...}
    end_list : ('air', 'door:')
    """
    node_lists = node_lists_from_node_dict(node_dict)
    send_node_lists(mc, node_lists, end_list)
