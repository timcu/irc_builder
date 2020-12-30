from ircbuilder import nodebuilder


class Building:
    """A Building allows user to create the whole structure before opening connection to IRC

    Example:

    import ircbuilder
    b = ircbuilder.Building()
    b.build(100, 14, 20, 'wool:green')
    with ircbuilder.open_irc('irc.triptera.com.au', 'mtuser', 'mtuserpass', 'mtbotnick', '#pythonator') as mc:
        b.send(mc)

    """
    def __init__(self):
        self.building = {}

    def build(self, x, y, z, item):
        """similar to set_node but stores nodes in building dict rather than sending to minetest

        x, y, z: coordinates to be added to nodes. They are converted to integers so that each node has unique set of coordinates
        item: minetest item name as a string "default:glass", or json string '{"name":"default:torch", "param2":"1"}'
        x, y, z can also be supplied as iterables eg range or list or tuple or generator
        """
        self.building.update(nodebuilder.build(x, y, z, item))

    def build_undo(self, x, y, z):
        """removes any nodes already built from building dict prior to sending to minetest

        x, y, z: coordinates to be added to nodes. They are converted to integers so that each node has unique set of coordinates
        x, y, z can also be supplied as iterables eg range or list or tuple or generator
        """
        for xi in nodebuilder.make_iter(x):
            for yi in nodebuilder.make_iter(y):
                for zi in nodebuilder.make_iter(z):
                    del self.building[nodebuilder.int_tuple(xi, yi, zi)]

    def send(self, minetest_connection, end_list=()):
        """sends building dict, which has been created from multiple calls to build(), to minetest

        end_list: order of items to send last. eg ("air", "default:torch")"""
        nodebuilder.send_node_dict(minetest_connection, self.building, end_list)
        self.building = {}

