import math
import socket
import json
import random
import string
import time
import zlib
import base64

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
    def __init__(self, ircserver, mtbotnick, port = 6667):
        self.ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ircsock.connect((ircserver, port)) # Here we connect to the server using the port 6667
        self.mtbotnick = mtbotnick
        self.channel = "##" + "".join(random.choice(string.ascii_letters) for _ in range(6))
        #print("Random channel", self.channel)

    def join_channel(self, channel):
        self.channel = channel
        self.send_string("JOIN "+ self.channel)

    def send_string(self, s):
        self.ircsock.send(encode(s.strip("\r\n") + "\n"))

    def response(self):
        self.ircsock.settimeout(15.0)
        try:
            ircmsg = self.ircsock.recv(2048).decode(CHAR_SET)
        except socket.timeout:
            #not interested in responses after 5 seconds
            print("socket.recv timed out!!")
            return ""
        ircmsg = ircmsg.strip('\r\n')
        if ircmsg.find("PING :") != -1:
            self.ping()
        if len(ircmsg):
            print(len(ircmsg), ircmsg)
        return ircmsg

    def send_msg(self, msg): # send private message to mtbotnick
        self.send_privmsg(self.channel + " :" + msg)

    def send_privmsg(self, msg): # send private message to mtbotnick
        self.send_string("PRIVMSG " + msg)

    def send_irccmd(self, msg): # send private message to mtbotnick
        #self.send_msg(self.mtbotnick + ': ' + msg) # displays in chat room
        self.send_privmsg(self.mtbotnick + ' : ' + msg) #doesn't display in chat room
        name = None
        response = self.response()
        start = time.time()
        while response.find("PRIVMSG") == -1 and time.time() - start < 5.0:
            response += self.response()
        #print("Time taken = " + str(time.time() - start))
        if response.find("PRIVMSG") != -1:
            # save user name into name variable
            name = response.split('!',1)[0][1:]
            # get the message to look for commands
            message = response.split('PRIVMSG',1)[1].split(':',1)[1]
        if (name == self.mtbotnick):
            return message
        return

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
            list_ret = ret.split(' ', maxsplit=1)
            try:
                count += int(list_ret[1])
            except ValueError:
                str_error += " [" + ret + "]"
            if len(list_ret) > 1 and list_ret[0] not in str_item:
                str_item += list_ret[0] + " "
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
        return self.send_cmd("get_ground_level " + str(math.floor(x)) + " " + str(math.floor(z)))

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

    @staticmethod
    def create(ircserver, mtuser, mtuserpass, mtbotnick = "mtserver", channel = "#coderdojo", pybotnick = None, port = 6667 ):
        mc = MinetestConnection(ircserver,mtbotnick,port)
        if not pybotnick:
            pybotnick = "py" + mtuser
            if len(pybotnick) > NICK_MAX_LEN: pybotnick = pybotnick[0:NICK_MAX_LEN]
        mc.send_string("USER " + pybotnick + " " + pybotnick + " " + pybotnick + " " + pybotnick) # user authentication
        mc.send_string("NICK " + pybotnick) # assign the nick to this python app
        mc.join_channel(channel)
        while mc.response().find("End of NAMES list") == -1:
            pass
        mc.send_irccmd("login " + mtuser + " " + mtuserpass)
        return mc


if __name__ == "__main__":
    mc = MinetestConnection.create("irc.undernet.org","serverop","")
    mc.send_privmsg("Hello, Minetest!")
