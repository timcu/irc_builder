dofile(minetest.get_modpath("ircbuilder") .. "/chatcmdbuilder.lua")

local get_ground_level = function(x, z)
	local y = 101
	local node
	local unground = {
		ignore=true, 
		air=true, 
		["default:tree"]=true, 
		["default:leaves"]=true,
	}
	repeat
		y = y - 1
		node = minetest.get_node({x=x,y=y,z=z})
		-- if map not loaded or generated yet node.name == 'ignore'
	until y < 0 or not unground[node.name]
	print(y, node.name)
	return y
end  

minetest.register_privilege("ircbuilder", {
    description = "Can use ircbuilder chat commands to set nodes from python/irc",
    give_to_singleplayer = true
})

ChatCmdBuilder.new("get_node", function(cmd)
	cmd:sub(":pos1:pos", function(name, pos1)
		local item = minetest.get_node(pos1)
		return true, minetest.write_json(item)
	end)
end, {
	description = 'pos, eg: "/get_node (1,8,1)". Should return something like {"name":"default:wood", "param2":"0"}',
	privs = {}
})

ChatCmdBuilder.new("get_ground_level", function(cmd)
	cmd:sub(":int:x :int:z", function(name, x, z)
		return true, ""..get_ground_level(x, z)
	end)
end, {
	description = 'x z, eg: "/get_ground_level 1 5". Returns max value of y that is not air leaves or tree',
	privs = {}
})

ChatCmdBuilder.new("get_connected_players", function(cmd)
	cmd:sub("", function(name, x, z)
		local response = ""
		local space = ""
		for _,player in ipairs(minetest.get_connected_players()) do
			response = response..space..player:get_player_name()
			space = " "
		end
		return true, response
	end)
end, {
	description = 'Returns list of connected players',
	privs = {}
})

ChatCmdBuilder.new("get_infotext", function(cmd)
	cmd:sub(":pos1:pos", function(name, pos1)
		local infotext = minetest.get_meta(pos1):get_string("infotext")
		return true, infotext
	end)
end, {
	description = "pos, eg: '/get_infotext (1,8,1)'. Returns text which displays when pointing at ",
	privs = {}
})

ChatCmdBuilder.new("get_meta", function(cmd)
	cmd:sub(":pos1:pos", function(name, pos1)
		local meta = minetest.get_meta(pos1)
		local metatable = meta:to_table()
		return true, minetest.write_json(metatable)
	end)
end, {
	description = "pos, eg: '/get_meta (1,8,1)'. Returns JSON object",
	privs = {}
})

-- function get_nodes is no longer used as response too long for irc
local get_nodes = function(name, pos1, pos2)
	local stepx = (pos1.x > pos2.x) and -1 or 1
	local stepy = (pos1.y > pos2.y) and -1 or 1
	local stepz = (pos1.z > pos2.z) and -1 or 1
	local response = "["
	local comma = ""
	for x = pos1.x,pos2.x,stepx do
		for y = pos1.y,pos2.y,stepy do
			for z = pos1.z,pos2.z,stepz do
				local pos = {x=x,y=y,z=z}
				local item=minetest.get_node(pos)
				local str_node = minetest.write_json({pos=pos,item=item})
				response = response..comma..str_node
				comma=","
			end
		end
	end
	return true, response.."]"
end
	
ChatCmdBuilder.new("compare_nodes", function(cmd)
	cmd:sub(":pos1:pos :pos2:pos :item:text", function(name, pos1, pos2, itemtext)
		local item
		if itemtext:sub(1,1) == "{" then
			item = json.decode(itemtext)
		else
			item = {name=itemtext}
		end
		local stepx = (pos1.x > pos2.x) and -1 or 1
		local stepy = (pos1.y > pos2.y) and -1 or 1
		local stepz = (pos1.z > pos2.z) and -1 or 1
		local count = 0
		for x = pos1.x,pos2.x,stepx do
			for y = pos1.y,pos2.y,stepy do
				for z = pos1.z,pos2.z,stepz do
					local pos = {x=x,y=y,z=z}
					local i=minetest.get_node(pos)
					local same = true
					for k,v in pairs(item) do
						if v ~= i[k] then
							same = false
						end
					end
					if not same then
						count = count + 1
					end
				end
			end
		end
		return true, ""..count
	end)
end, {
	description = [[pos1 pos2 item
	eg: 
	/compare_nodes (1,8,1) (2,9,2) "wool:orange"
	/compare_nodes (1,8,1) (2,9,2) {"name":"wool:orange", "param2":"0"}
	Returns count of nodes which differ from specified item attributes
	Unspecified attributes are not differences]],
	privs = {}
})

ChatCmdBuilder.new("set_node", function(cmd)
	cmd:sub(":pos1:pos :item:text", function(name, pos1, itemtext)
		local item
		if itemtext:sub(1,1) == "{" then
			item = minetest.parse_json(itemtext)
		else
			item = {name=itemtext}
		end
		minetest.set_node(pos1, item)
		return true, itemtext .." 1"
	end)
end, {
	description = "pos item, eg: /set_node (1,8,1) default:stone",
	privs = {ircbuilder = true}
})

ChatCmdBuilder.new("set_nodes", function(cmd)
	cmd:sub(":pos1:pos :pos2:pos :item:text", function(name, pos1, pos2, itemtext)
		local stepx = (pos1.x > pos2.x) and -1 or 1
		local stepy = (pos1.y > pos2.y) and -1 or 1
		local stepz = (pos1.z > pos2.z) and -1 or 1
		local count = 0
		local item
		if itemtext:sub(1,1) == "{" then
			item = minetest.parse_json(itemtext)
		else
			item = {name=itemtext}
		end
		for x = pos1.x,pos2.x,stepx do
			for y = pos1.y,pos2.y,stepy do
				for z = pos1.z,pos2.z,stepz do
					minetest.set_node({x=x,y=y,z=z},item)
					count = count + 1
				end
			end
		end
		return true, itemtext.." "..count
	end)
end, {
	description = "pos1 pos2 item, eg: /set_nodes (1,8,1) (2,9,2) wool:orange",
	privs = {ircbuilder = true}
})

ChatCmdBuilder.new("set_sign", function(cmd)
	cmd:sub(":pos:pos :direction:word :itemname:word :text:text", function(name, pos, direction, itemname, text)
		local reg=minetest.registered_nodes[itemname]
		if not reg then
			return false,"Sign type not registered: "..itemname
		end
		text=text:gsub("\\n","\n")
		local d=direction:lower()
		if d=="+x" then dir={x=1,y=0,z=0}
		elseif d=="-x" then dir={x=-1,y=0,z=0}
		elseif d=="+y" then dir={x=0,y=1,z=0}
		elseif d=="-y" then dir={x=0,y=-1,z=0}
		elseif d=="+z" then dir={x=0,y=0,z=1}
		elseif d=="-z" then dir={x=0,y=0,z=-1}
		else return false,"Unknown direction descriptor: "..d
		end
		local sign={name=itemname}
		if reg.paramtype2=="wallmounted" then
			sign.param2=minetest.dir_to_wallmounted(dir)
		elseif reg.paramtype2=="facedir" then 
			sign.param2=minetest.dir_to_facedir(dir)
		else
			return false,"Unknown paramtype2: "..reg.paramtype2
		end
		minetest.add_node(pos, sign)
		local meta = minetest.get_meta(pos)
		meta:set_string("text",text)
		return true, itemname
	end)
end, {
	description = [[pos direction itemname text
	eg: 
	/set_sign (1,8,1) +x default:sign_wall_wood This is\nmy #4red sign]],
	privs = {ircbuilder = true}
})

ChatCmdBuilder.new("add_book_to_chest", function(cmd)
	cmd:sub(":pos:pos :text:text", function(name, pos, text)
		local itemname="default:book_written"
		local reg=minetest.registered_craftitems[itemname]
		if not reg then
			return false,"Book type not registered: "..itemname
		end
		text=text:gsub("\\n","\n")
		local texttable
		if text:sub(1,1) == "{" then
			texttable=minetest.parse_json(text)
		else
			texttable={title=name.."'s book", text=text}
		end
		local book = ItemStack(itemname)
		local bookmeta = book:get_meta()
		for k,v in pairs(texttable) do
			bookmeta:set_string(k,v)
		end
		bookmeta:set_string('owner',name)
		bookmeta:set_string('text_len',""..texttable.text:len())
		bookmeta:set_string('page_max',"1")
		bookmeta:set_string('description',name.."'s book")
		--local tnew = book:to_table()
		--print(minetest.serialize(tnew))
		
		local chestname="default:chest"
		local currentnode=minetest.get_node(pos)
		if currentnode.name ~= chestname then
			minetest.set_node(pos,{name=chestname})
		end
		local meta=minetest.get_meta(pos)
		local invref = meta:get_inventory()
		invref:add_item("main",book)
		--local list=invref:get_list("main")
		--book=invref:get_stack("main",3)
		--local t = book:to_table()
		--print(minetest.serialize(t))
		return true, itemname
	end)
end, {
	description = [[pos text
	eg: 
	/add_book_to_chest (1,8,1) This is\nmy book text]],
	privs = {ircbuilder = true}
})


				
