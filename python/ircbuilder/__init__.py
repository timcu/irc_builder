import math
import socket
import json
import random
import string
import time
import zlib
import base64
import sys
import queue
import threading
from .version import VERSION
import ircbuilder.nodebuilder as nodebuilder

NICK_MAX_LEN=9
CHAR_SET="UTF-8"

def strxyz(x, y, z):
    return "(" + str(x) + "," + str(y) + "," + str(z) + ") "


def strxyzint(x, y, z):
    return strxyz(math.floor(x+0.5), math.floor(y+0.5), math.floor(z+0.5))


def encode(s):
    return bytes(s, CHAR_SET)


def escape(s):
    """Escape content of strings which will break the api using html entity type escaping"""
    s = s.replace("&","&amp;")
    s = s.replace("\r\n","&#10;")
    s = s.replace("\n","&#10;")
    s = s.replace("\r","&#10;")
    s = s.replace("(","&#40;")
    s = s.replace(")","&#41;")
    s = s.replace(",","&#44;")
    s = s.replace("§","&sect;")
    return s


class MinetestConnection:
    """Connection to IRC Server sending commands to Minetest"""
    def __init__(self, ircserver, mtbotnick, pybotnick, port = 6667):
        self.ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ircsock.connect((ircserver, port)) # Here we connect to the server using the port 6667
        self.mtbotnick = mtbotnick
        self.pybotnick = pybotnick
        self.channel = "##" + "".join(random.choice(string.ascii_letters) for _ in range(6))
        # print("Random channel", self.channel)
        self.pycharm_edu_check_task = len(sys.argv) > 1 and "_window" in sys.argv[1]
        # self.pycharm_edu_check_task = True  # For testing only
        self.irc_disabled_message = "IRC disabled because sys.argv[1] contains '_window' meaning PyCharm Edu is checking task"
        # self.irc_disabled_message_printed = False
        self.ircserver = ircserver
        self.ircserver_name = None
        # building is a node dict which stores results of build commands before sending to minetest in a batch
        self.building = {}
        self.q_msg = queue.Queue()
        self.q_num = queue.Queue()
        self.receive_thread = threading.Thread(target=self.receive_irc)
        # Set daemon so thread will stop when main program stops
        self.receive_thread.setDaemon(True)
        self.receive_thread.start()


    def join_channel(self, channel=None):
        if channel:
            # if channel not set, use randomly generated channel
            self.channel = channel
        else:
            print("Joining IRC channel " + self.channel)
        self.send_string("JOIN "+ self.channel)

    def send_string(self, s):
        if self.pycharm_edu_check_task:
            if not self.irc_disabled_message_printed:
                print(self.irc_disabled_message)
                self.irc_disabled_message_printed = True
            return
        print("SENDING:",s)
        self.ircsock.send(encode(s.strip("\r\n") + "\n"))
    
    def pong(self, *items):
        items = ['PONG'] + [x for x in items if x is not None]
        self.send_string(' '.join(items))

    def receive_irc(self):
        if self.pycharm_edu_check_task:
            print(self.irc_disabled_message)
            if self.q_msg.empty():
                self.q_msg.put(self.irc_disabled_message)
            return

        buffer = ''
        while True:
            try:
                buffer += self.ircsock.recv(2048).decode(CHAR_SET)
            except socket.timeout:
                print("socket.recv timed out!!")
            last_line_complete = len(buffer)>0 and buffer[-1:] in ('\r\n')
            lines = buffer.split('\r\n')
            if not last_line_complete:
                buffer = lines[-1]
                del(lines[-1])
            else:
                buffer = ''
            for line in lines:
                print("LINE: " + str(line))
                if line.find("PING :") == 0:
                    self.pong(line[6:])
                elif line.find("VERSION") == 0:
                    self.send_string("VERSION python ircbuilder " + VERSION)
                else:
                    if line.startswith(':'):
                        parts = line[1:].split(' ', maxsplit=3)
                        # 0: sender
                        # 1: PRIVMSG
                        # 2: recipient
                        # 3: message (starting with a :)
                        sender = parts[0]
                        sender_name = sender.split('!',1)[0]
                        if not self.ircserver_name:
                            self.ircserver_name = sender_name
                        recipient_name = parts[2]
                        # print("SENDER:",sender_name,self.ircserver_name,"RECIPIENT:",recipient_name,self.pybotnick)
                        if recipient_name == self.pybotnick:
                            if parts[1] == "PRIVMSG" and parts[3] == ":\x01VERSION\x01":
                                self.send_string("VERSION python ircbuilder " + VERSION)
                            if sender_name == self.ircserver_name:
                                try:
                                    message_num = int(parts[1])
                                except ValueError:
                                    message_num = None
                                if message_num:
                                    self.q_num.put(message_num)
                                    # print("Queued msg_num:",parts[1])
                            elif sender_name == self.mtbotnick:
                                if parts[1] == "PRIVMSG":
                                    # get the message to look for commands
                                    message = parts[3].split(':',1)[1]
                                    self.q_msg.put(message)
                                    # print("Queued message:",message)

    def send_msg(self, msg): # send private message to mtbotnick
        self.send_privmsg(self.channel + " :" + msg)

    def send_privmsg(self, msg): # send private message to mtbotnick
        self.send_string("PRIVMSG " + msg)

    def wait_for_privmsg(self, timeout=5.0):
        start = time.time()
        while time.time() - start < timeout:
            if not self.q_msg.empty():
                return self.q_msg.get()
            else:
                time.sleep(0.1)
        print("Timeout waiting for privmsg " + str(time.time() - start))
        return

    def wait_for_message_num(self, message_num, timeout=15.0):
        start = time.time()
        while time.time() - start < timeout:
            if not self.q_num.empty():
                num = self.q_num.get()
                if message_num == num or num >= 400:
                    # print("Seconds", (time.time()-start), "waiting for", message_num , "and found", num)
                    return num
            else:
                time.sleep(0.1)
        print("Timeout waiting for", message_num)
        return None


    def send_irccmd(self, msg): # send private message to mtbotnick
        #self.send_msg(self.mtbotnick + ': ' + msg) # displays in chat room
        self.send_privmsg(self.mtbotnick + ' : ' + msg) #doesn't display in chat room
        return self.wait_for_privmsg()

    def send_cmd(self, msg): # send private message to mtbotnick
        return self.send_irccmd("cmd " + msg)

    def get_node(self, x, y, z):
        """Get block (x,y,z) => item:string"""
        return self.send_cmd("get_node " + strxyzint(x, y, z))

    def compare_nodes(self, x1, y1, z1, x2, y2, z2, item):
        """Compare a cuboid of blocks (x1, y1, z1, x2, y2, z2) with an item => count of differences"""
        return self.send_cmd("compare_nodes " + strxyzint(x1, y1, z1) + strxyzint(x2, y2, z2) + " " + item)

    def set_node(self, x, y, z, item):
        """Set block (x, y, z, item)"""
        return self.send_cmd("set_node " + strxyzint(x, y, z) + item)

    def set_nodes(self, x1, y1, z1, x2, y2, z2, item):
        """Set a cuboid of blocks (x1, y1, z1, x2, y2, z2, item)"""
        return self.send_cmd("set_nodes " + strxyzint(x1, y1, z1) + strxyzint(x2, y2, z2) + item)

    def set_node_list(self, list_pos, item):
        """Set all blocks at a list of position tuples to the same item ([(x1, y1, z1), (x2, y2, z2), ...], item)"""
        batches = 0
        maxperbatch = 0
        while batches==0 or maxperbatch > 400:
            maxperbatch = 0
            batches += 1
            batch_size = len(list_pos) // batches + 1
            b64=[]
            for batch in range(batches):
                beg = batch * batch_size
                end = beg + batch_size
                s = '|'
                for pos in list_pos[beg:end]:
                    if len(pos) == 2 and len(pos[0])==3 and len(pos[1])==3:
                        s = s + strxyzint(pos[0][0],pos[0][1],pos[0][2]).strip("() ") + " "
                        s = s + strxyzint(pos[1][0],pos[1][1],pos[1][2]).strip("() ") + "|"
                    else:
                        s = s + strxyzint(pos[0],pos[1],pos[2]).strip("() ") + "|"
                #print(s)
                bytes_unzipped=s.encode('utf-8')
                bytes_zipped=zlib.compress(bytes_unzipped)
                b64.append(base64.standard_b64encode(bytes_zipped).decode('utf-8') + " ")
                lenxmit = len("set_node_list " + b64[batch] + item)
                if maxperbatch < lenxmit:
                    maxperbatch = lenxmit
                #print("Batch",batch,"of",batches,"from",beg,"to",end,"len",lenxmit)
        str_error = ''
        str_item = ''
        count = 0
        for batch in range(batches):
            ret = self.send_cmd("set_node_list " + b64[batch] + item)
            try:
                list_ret = ret.split(' ', maxsplit=1)
                count += int(list_ret[1])
                if len(list_ret) > 1 and list_ret[0] not in str_item:
                    str_item += list_ret[0] + " "
            except AttributeError:
                # list_ret is None so can't be split
                pass
            except ValueError:
                str_error += " [" + ret + "]"
        return str_item + str(count) + str_error

    def set_sign(self, x, y, z, direction, text, type="default:sign_wall_wood"):
        """Set a sign at a location with text and facing direction

        sign_node: "default:sign_wall_wood"
        text:"#0Formatted body #3of\n#1text"
        direction: "+x" or "-x" or "+y" or "-y" or "+z" or "-z" : Which way user is facing to read sign
        Example sign_node names:
        default:sign_wall_wood
        default:sign_wall_steel
        signs:sign_hanging
        signs:sign_yard
        signs:sign_wall_green
        signs:sign_wall_yellow
        signs:sign_wall_red
        signs:sign_wall_white_red
        signs:sign_wall_white_black
        signs:sign_wall_orange
        signs:sign_wall_blue
        signs:sign_wall_brown
        locked_sign:sign_wall_locked
        Can also mount signs on fences"""
        #dirx, diry, dirz (facing direction vector): 0,0,-1
        #param1: lower 4 bits daylight, upper 4 bits nightlight. Don't specify or use 15 for all signs except hanging which are 13
        #param2 (facedir): 0=z, 1=x, 2=-z, 3=-x
        #param2 (wallmounted): 0=y, 1=-y, 2=x, 3=-x, 4=z, 5=-z
        return self.send_cmd("set_sign " + strxyzint(x, y, z) + " " + direction + " " + type + " " + text.replace("\r","").replace("\n","\\n"))

    def set_sign_wall(self, x, y, z, direction, text):
        return self.set_sign(x, y, z, direction, text, "default:sign_wall_wood")

    def set_sign_yard(self, x, y, z, direction, text):
        return self.set_sign(x, y, z, direction, text, "signs:sign_yard")

    def book(title, text):
        book = {}
        book['title'] = title
        book['text'] = text
        return book

    def add_book_to_chest(self, x, y, z, book):
        """Add a book to a chest (x,y,z,book)

        The location x,y,z must contain a chest or other Inventory Holder
        book is a JSON string or mcpi.book.Book object describing the book
        @author: Tim Cummings https://www.triptera.com.au/wordpress/"""
        return self.send_cmd("add_book_to_chest " + strxyzint(x, y, z) + json.dumps(book).replace("\r","").replace("\n","\\n"))

    def get_ground_level(self, x, z):
        return int(self.send_cmd("get_ground_level " + str(math.floor(x+0.5)) + " " + str(math.floor(z+0.5))))

    def get_connected_players(self):
        return self.send_cmd("get_connected_players").split(" ")

    #Following deprecated and provided for backward compatibility only
    def getBlock(self, x, y, z):
        return self.get_node(x, y, z)

    #def getBlocks(self, x1, y1, z1, x2, y2, z2):
    #    return self.get_nodes(x1, y1, z1, x2, y2, z2)

    def setBlock(self, x, y, z, item):
        return self.set_node(x, y, z, item)

    def setBlocks(self, x1, y1, z1, x2, y2, z2, item):
        return self.set_nodes(x1, y1, z1, x2, y2, z2, item)

    def addBookToChest(self, x, y, z, book):
        return self.add_book_to_chest(x, y, z, book)

    def spawnEntity(self, x,y,z,entity):
        """Spawn entity (x,y,z,id,[data])"""
        return self.send_cmd("spawnentity " + entity + strxyz(x,y,z))

    def getHeight(self, x, z):
        """Get the height of the world (x,z) => int"""
        return self.get_ground_level(x, z)

    def getPlayerEntityIds(self):
        """Get the entity ids of the connected players => [id:int]"""
        #ids = self.conn.sendReceive(b"world.getPlayerIds")
        #return list(map(int, ids.split("|")))
        return self.get_connected_players()

    #def getPlayerEntityId(self, name):
    #    """Get the entity id of the named player => [id:int]"""
    #    return int(self.conn.sendReceive(b"world.getPlayerId", name))

#    def saveCheckpoint(self):
#        """Save a checkpoint that can be used for restoring the world"""
#        self.conn.send(b"world.checkpoint.save")

#    def restoreCheckpoint(self):
#        """Restore the world state to the checkpoint"""
#        self.conn.send(b"world.checkpoint.restore")

    def postToChat(self, msg):
        """Post a message to the game chat"""
        self.send_privmsg(msg)

#    def setting(self, setting, status):
#        """Set a world setting (setting, status). keys: world_immutable, nametags_visible"""
#        self.conn.send(b"world.setting", setting, 1 if bool(status) else 0)

#    def getEntityTypes(self):
#        """Return a list of Entity objects representing all the entity types in Minecraft"""
#        s = self.conn.sendReceive(b"world.getEntityTypes")
#        types = [t for t in s.split("|") if t]
#        return [Entity(int(e[:e.find(",")]), e[e.find(",") + 1:]) for e in types]

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

    def send_building(self, end_list=()):
        """sends building dict, which has been created from multiple calls to build(), to minetest

        end_list: order of items to send last. eg ("air", "default:torch")"""
        nodebuilder.send_node_dict(self, self.building, end_list)
        self.building = {}

    @staticmethod
    def create(ircserver, mtuser, mtuserpass, mtbotnick = "mtserver", channel = None, pybotnick = None, port = 6667 ):
        if not pybotnick:
            pybotnick = "py" + mtuser
            if len(pybotnick) > NICK_MAX_LEN: pybotnick = pybotnick[0:NICK_MAX_LEN]
        mc = MinetestConnection(ircserver,mtbotnick,pybotnick,port)
        #mc.send_string("USER " + pybotnick + " " + pybotnick + " " + pybotnick + " " + pybotnick) # user authentication
        mc.send_string("USER " + pybotnick + " 0 * :" + pybotnick) # user authentication  first pybotnick is username, second pybotnick is real name
        mc.send_string("NICK " + pybotnick) # assign the nick to this python app
        mc.wait_for_message_num(376) # End of MOTD
        mc.join_channel(channel)
        mc.wait_for_message_num(366) # End of NAMES list
        #start = time.time()
        #while mc.response().find("End of NAMES list") == -1 and time.time() - start < 5.0 and not mc.pycharm_edu_check_task:
        #    time.sleep(1)
        mc.send_irccmd("login " + mtuser + " " + mtuserpass)
        return mc


if __name__ == "__main__":
    mc = MinetestConnection.create("irc.rizon.net","serverop",sys.argv[0])
    mc.send_privmsg("Hello, Minetest!")
