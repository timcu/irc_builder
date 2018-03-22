--[[

Extract from https://github.com/davidm/lua-compress-deflatelua

deflate (and gunzip/zlib) implemented in Lua.

SYNOPSIS
  can uncompress from string including zlib and raw DEFLATE formats.
  
DESCRIPTION
  
  This is a pure Lua implementation of decompressing the DEFLATE format,
  including the related zlib and gzip formats.
  
  Note: This library only supports decompression.
  Compression is not currently implemented.
API
  Note: in the following functions, input stream `fh` may be
  a file handle, string, or an iterator function that returns strings.
  Output stream `ofh` may be a file handle or a function that
  consumes one byte (number 0..255) per call.
  DEFLATE.inflate {input=fh, output=ofh}
    Decompresses input stream `fh` in the DEFLATE format
    while writing to output stream `ofh`.
    DEFLATE is detailed in http://tools.ietf.org/html/rfc1951 .
  
  DEFLATE.gunzip {input=fh, output=ofh, disable_crc=disable_crc}
  
    Decompresses input stream `fh` with the gzip format
    while writing to output stream `ofh`.
    `disable_crc` (defaults to `false`) will disable CRC-32 checking
    to increase speed.
    gzip is detailed in http://tools.ietf.org/html/rfc1952 .
  DEFLATE.inflate_zlib {input=fh, output=ofh, disable_crc=disable_crc}
  
    Decompresses input stream `fh` with the zlib format
    while writing to output stream `ofh`.
    `disable_crc` (defaults to `false`) will disable CRC-32 checking
    to increase speed.
    zlib is detailed in http://tools.ietf.org/html/rfc1950 .  
  DEFLATE.adler32(byte, crc) --> rcrc
  
    Returns adler32 checksum of byte `byte` (number 0..255) appended
    to string with adler32 checksum `crc`.  This is internally used by
    `inflate_zlib`.
    ADLER32 in detailed in http://tools.ietf.org/html/rfc1950 .

DEPENDENCIES
  None in this extracted file which only decompresses strings of data

LICENSE
  (c) 2008-2011 David Manura.  Licensed under the same terms as Lua (MIT).
  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:
  The above copyright notice and this permission notice shall be included in
  all copies or substantial portions of the Software.
  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
  THE SOFTWARE.
  (end license)
--]]

local M = {
	--_TYPE='module', 
	--_NAME='compress.deflatelua', 
	_VERSION='0.3.20111128'
}

local assert = assert
local error = error
local ipairs = ipairs
local pairs = pairs
local print = print
local require = require
local tostring = tostring
local type = type
local setmetatable = setmetatable
local io = io
local math = math
local table_sort = table.sort
local math_max = math.max
local string_char = string.char

local NATIVE_BITOPS = false
local DEBUG = false

local band, lshift, rshift

local function warn(s)
  io.stderr:write(s, '\n')
end


local function debug(...)
  print('DEBUG', ...)
end


local function runtime_error(s, level)
  level = level or 1
  error({s}, level+1)
end


local function make_outstate(outbs)
  local outstate = {}
  outstate.outbs = outbs
  outstate.window = {}
  outstate.window_pos = 1
  return outstate
end


local function output(outstate, byte)
  -- debug('OUTPUT:', s)
  local window_pos = outstate.window_pos
  outstate.outbs(byte)
  outstate.window[window_pos] = byte
  outstate.window_pos = window_pos % 32768 + 1  -- 32K
end


local function noeof(val)
  return assert(val, 'unexpected end of file')
end


local function hasbit(bits, bit)
  return bits % (bit + bit) >= bit
end


local function memoize(f)
  local mt = {}
  local t = setmetatable({}, mt)
  function mt:__index(k)
    local v = f(k)
    t[k] = v
    return v
  end
  return t
end


-- small optimization (lookup table for powers of 2)
local pow2 = memoize(function(n) return 2^n end)


-- weak metatable marking objects as bitstream type
local is_bitstream = setmetatable({}, {__mode='k'})


local function bytestream_from_string(s)
  local i = 1
  local o = {}
  function o:read()
    local by
    if i <= #s then
      by = s:byte(i)
      i = i + 1
    end
    return by
  end
  return o
end


local function bytestream_from_function(f)
  local i = 0
  local buffer = ''
  local o = {}
  function o:read()
    i = i + 1
    if i > #buffer then
      buffer = f()
      if not buffer then return end
      i = 1
    end
    return buffer:byte(i,i)
  end
  return o
end


local function bitstream_from_bytestream(bys)
  local buf_byte = 0
  local buf_nbit = 0
  local o = {}

  function o:nbits_left_in_byte()
    return buf_nbit
  end

  if NATIVE_BITOPS then
    function o:read(nbits)
      nbits = nbits or 1
      while buf_nbit < nbits do
        local byte = bys:read()
        if not byte then return end  -- note: more calls also return nil
        buf_byte = buf_byte + lshift(byte, buf_nbit)
        buf_nbit = buf_nbit + 8
      end
      local bits
      if nbits == 0 then
        bits = 0
      elseif nbits == 32 then
        bits = buf_byte
        buf_byte = 0
      else
        bits = band(buf_byte, rshift(0xffffffff, 32 - nbits))
        buf_byte = rshift(buf_byte, nbits)
      end
      buf_nbit = buf_nbit - nbits
      return bits
    end
  else
    function o:read(nbits)
      nbits = nbits or 1
      while buf_nbit < nbits do
        local byte = bys:read()
        if not byte then return end  -- note: more calls also return nil
        buf_byte = buf_byte + pow2[buf_nbit] * byte
        buf_nbit = buf_nbit + 8
      end
      local m = pow2[nbits]
      local bits = buf_byte % m
      buf_byte = (buf_byte - bits) / m
      buf_nbit = buf_nbit - nbits
      return bits
    end
  end
  
  is_bitstream[o] = true

  return o
end


local function get_bitstream(o)
  local bs
  if is_bitstream[o] then
    return o
  elseif io.type(o) == 'file' then
    bs = bitstream_from_bytestream(bytestream_from_file(o))
  elseif type(o) == 'string' then
    bs = bitstream_from_bytestream(bytestream_from_string(o))
  elseif type(o) == 'function' then
    bs = bitstream_from_bytestream(bytestream_from_function(o))
  else
    runtime_error 'unrecognized type'
  end
  return bs
end


local function get_obytestream(o)
  local bs
  if io.type(o) == 'file' then
    bs = function(sbyte) o:write(string_char(sbyte)) end
  elseif type(o) == 'function' then
    bs = o
  else
    runtime_error('unrecognized type: ' .. tostring(o))
  end
  return bs
end


local function HuffmanTable(init, is_full)
  local t = {}
  if is_full then
    for val,nbits in pairs(init) do
      if nbits ~= 0 then
        t[#t+1] = {val=val, nbits=nbits}
        --debug('*',val,nbits)
      end
    end
  else
    for i=1,#init-2,2 do
      local firstval, nbits, nextval = init[i], init[i+1], init[i+2]
      --debug(val, nextval, nbits)
      if nbits ~= 0 then
        for val=firstval,nextval-1 do
          t[#t+1] = {val=val, nbits=nbits}
        end
      end
    end
  end
  table_sort(t, function(a,b)
    return a.nbits == b.nbits and a.val < b.val or a.nbits < b.nbits
  end)

  -- assign codes
  local code = 1  -- leading 1 marker
  local nbits = 0
  for i,s in ipairs(t) do
    if s.nbits ~= nbits then
      code = code * pow2[s.nbits - nbits]
      nbits = s.nbits
    end
    s.code = code
    --debug('huffman code:', i, s.nbits, s.val, code, bits_tostring(code))
    code = code + 1
  end

  local minbits = math.huge
  local look = {}
  for i,s in ipairs(t) do
    minbits = math.min(minbits, s.nbits)
    look[s.code] = s.val
  end

  --for _,o in ipairs(t) do
  --  debug(':', o.nbits, o.val)
  --end

  -- function t:lookup(bits) return look[bits] end

  local msb = NATIVE_BITOPS and function(bits, nbits)
    local res = 0
    for i=1,nbits do
      res = lshift(res, 1) + band(bits, 1)
      bits = rshift(bits, 1)
    end
    return res
  end or function(bits, nbits)
    local res = 0
    for i=1,nbits do
      local b = bits % 2
      bits = (bits - b) / 2
      res = res * 2 + b
    end
    return res
  end
  
  local tfirstcode = memoize(
    function(bits) return pow2[minbits] + msb(bits, minbits) end)

  function t:read(bs)
    local code = 1 -- leading 1 marker
    local nbits = 0
    while 1 do
      if nbits == 0 then  -- small optimization (optional)
        code = tfirstcode[noeof(bs:read(minbits))]
        nbits = nbits + minbits
      else
        local b = noeof(bs:read())
        nbits = nbits + 1
        code = code * 2 + b   -- MSB first
        --[[NATIVE_BITOPS
        code = lshift(code, 1) + b   -- MSB first
        --]]
      end
      --debug('code?', code, bits_tostring(code))
      local val = look[code]
      if val then
        --debug('FOUND', val)
        return val
      end
    end
  end

  return t
end


local function parse_zlib_header(bs)
  local cm = bs:read(4) -- Compression Method
  local cinfo = bs:read(4) -- Compression info
  local fcheck = bs:read(5) -- FLaGs: FCHECK (check bits for CMF and FLG)
  local fdict = bs:read(1) -- FLaGs: FDICT (present dictionary)
  local flevel = bs:read(2) -- FLaGs: FLEVEL (compression level)
  local cmf = cinfo * 16  + cm -- CMF (Compresion Method and flags)
  local flg = fcheck + fdict * 32 + flevel * 64 -- FLaGs
  
  if cm ~= 8 then -- not "deflate"
    runtime_error("unrecognized zlib compression method: " + cm)
  end
  if cinfo > 7 then
    runtime_error("invalid zlib window size: cinfo=" + cinfo)
  end
  local window_size = 2^(cinfo + 8)
  
  if (cmf*256 + flg) %  31 ~= 0 then
    runtime_error("invalid zlib header (bad fcheck sum)")
  end
  
  if fdict == 1 then
    runtime_error("FIX:TODO - FDICT not currently implemented")
    local dictid_ = bs:read(32)
  end
  
  return window_size
end


local function parse_huffmantables(bs)
    local hlit = bs:read(5)  -- # of literal/length codes - 257
    local hdist = bs:read(5) -- # of distance codes - 1
    local hclen = noeof(bs:read(4)) -- # of code length codes - 4

    local ncodelen_codes = hclen + 4
    local codelen_init = {}
    local codelen_vals = {
      16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15}
    for i=1,ncodelen_codes do
      local nbits = bs:read(3)
      local val = codelen_vals[i]
      codelen_init[val] = nbits
    end
    local codelentable = HuffmanTable(codelen_init, true)

    local function decode(ncodes)
      local init = {}
      local nbits
      local val = 0
      while val < ncodes do
        local codelen = codelentable:read(bs)
        --FIX:check nil?
        local nrepeat
        if codelen <= 15 then
          nrepeat = 1
          nbits = codelen
          --debug('w', nbits)
        elseif codelen == 16 then
          nrepeat = 3 + noeof(bs:read(2))
          -- nbits unchanged
        elseif codelen == 17 then
          nrepeat = 3 + noeof(bs:read(3))
          nbits = 0
        elseif codelen == 18 then
          nrepeat = 11 + noeof(bs:read(7))
          nbits = 0
        else
          error 'ASSERT'
        end
        for i=1,nrepeat do
          init[val] = nbits
          val = val + 1
        end
      end
      local huffmantable = HuffmanTable(init, true)
      return huffmantable
    end

    local nlit_codes = hlit + 257
    local ndist_codes = hdist + 1

    local littable = decode(nlit_codes)
    local disttable = decode(ndist_codes)

    return littable, disttable
end


local tdecode_len_base
local tdecode_len_nextrabits
local tdecode_dist_base
local tdecode_dist_nextrabits
local function parse_compressed_item(bs, outstate, littable, disttable)
  local val = littable:read(bs)
  --debug(val, val < 256 and string_char(val))
  if val < 256 then -- literal
    output(outstate, val)
  elseif val == 256 then -- end of block
    return true
  else
    if not tdecode_len_base then
      local t = {[257]=3}
      local skip = 1
      for i=258,285,4 do
        for j=i,i+3 do t[j] = t[j-1] + skip end
        if i ~= 258 then skip = skip * 2 end
      end
      t[285] = 258
      tdecode_len_base = t
      --for i=257,285 do debug('T1',i,t[i]) end
    end
    if not tdecode_len_nextrabits then
      local t = {}
      if NATIVE_BITOPS then
        for i=257,285 do
          local j = math_max(i - 261, 0)
          t[i] = rshift(j, 2)
        end
      else
        for i=257,285 do
          local j = math_max(i - 261, 0)
          t[i] = (j - (j % 4)) / 4
        end
      end
      t[285] = 0
      tdecode_len_nextrabits = t
      --for i=257,285 do debug('T2',i,t[i]) end
    end
    local len_base = tdecode_len_base[val]
    local nextrabits = tdecode_len_nextrabits[val]
    local extrabits = bs:read(nextrabits)
    local len = len_base + extrabits

    if not tdecode_dist_base then
      local t = {[0]=1}
      local skip = 1
      for i=1,29,2 do
        for j=i,i+1 do t[j] = t[j-1] + skip end
        if i ~= 1 then skip = skip * 2 end
      end
      tdecode_dist_base = t
      --for i=0,29 do debug('T3',i,t[i]) end
    end
    if not tdecode_dist_nextrabits then
      local t = {}
      if NATIVE_BITOPS then
        for i=0,29 do
          local j = math_max(i - 2, 0)
          t[i] = rshift(j, 1)
        end
      else
        for i=0,29 do
          local j = math_max(i - 2, 0)
          t[i] = (j - (j % 2)) / 2
        end
      end
      tdecode_dist_nextrabits = t
      --for i=0,29 do debug('T4',i,t[i]) end
    end
    local dist_val = disttable:read(bs)
    local dist_base = tdecode_dist_base[dist_val]
    local dist_nextrabits = tdecode_dist_nextrabits[dist_val]
    local dist_extrabits = bs:read(dist_nextrabits)
    local dist = dist_base + dist_extrabits

    --debug('BACK', len, dist)
    for i=1,len do
      local pos = (outstate.window_pos - 1 - dist) % 32768 + 1  -- 32K
      output(outstate, assert(outstate.window[pos], 'invalid distance'))
    end
  end
  return false
end


local function parse_block(bs, outstate)
  local bfinal = bs:read(1)
  local btype = bs:read(2)

  local BTYPE_NO_COMPRESSION = 0
  local BTYPE_FIXED_HUFFMAN = 1
  local BTYPE_DYNAMIC_HUFFMAN = 2
  local BTYPE_RESERVED_ = 3

  if DEBUG then
    debug('bfinal=', bfinal)
    debug('btype=', btype)
  end

  if btype == BTYPE_NO_COMPRESSION then
    bs:read(bs:nbits_left_in_byte())
    local len = bs:read(16)
    local nlen_ = noeof(bs:read(16))

    for i=1,len do
      local by = noeof(bs:read(8))
      output(outstate, by)
    end
  elseif btype == BTYPE_FIXED_HUFFMAN or btype == BTYPE_DYNAMIC_HUFFMAN then
    local littable, disttable
    if btype == BTYPE_DYNAMIC_HUFFMAN then
      littable, disttable = parse_huffmantables(bs)
    else
      littable  = HuffmanTable {0,8, 144,9, 256,7, 280,8, 288,nil}
      disttable = HuffmanTable {0,5, 32,nil}
    end

    repeat
      local is_done = parse_compressed_item(
        bs, outstate, littable, disttable)
    until is_done
  else
    runtime_error 'unrecognized compression type'
  end

  return bfinal ~= 0
end


function M.inflate(t)
  local bs = get_bitstream(t.input)
  local outbs = get_obytestream(t.output)
  local outstate = make_outstate(outbs)

  repeat
    local is_final = parse_block(bs, outstate)
  until is_final
end
local inflate = M.inflate

function M.inflate_zlib(t)
  local bs = get_bitstream(t.input)
  local outbs = get_obytestream(t.output)
  local disable_crc = t.disable_crc
  if disable_crc == nil then disable_crc = false end
  
  local window_size_ = parse_zlib_header(bs)
  
  local data_adler32 = 1
  
  inflate{input=bs, output=
    disable_crc and outbs or
      function(byte)
        data_adler32 = M.adler32(byte, data_adler32)
        outbs(byte)
      end
  }

  bs:read(bs:nbits_left_in_byte())
  
  local b3 = bs:read(8)
  local b2 = bs:read(8)
  local b1 = bs:read(8)
  local b0 = bs:read(8)
  local expected_adler32 = ((b3*256 + b2)*256 + b1)*256 + b0
  if DEBUG then
    debug('alder32=', expected_adler32)
  end
  if not disable_crc then
    if data_adler32 ~= expected_adler32 then
      runtime_error('invalid compressed data--crc error')
    end    
  end
  if bs:read() then
    warn 'trailing garbage ignored'
  end
end


function M.inflate_zlib_nocrc(t)
  t.disable_crc = true
  M.inflate_zlib(t)
end


--return M
-- decoding base64 from http://lua-users.org/wiki/BaseSixtyFour
local standard_b64decode = function(data)
	local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    data = string.gsub(data, '[^'..b..'=]', '')
    return (data:gsub('.', function(x)
        if (x == '=') then return '' end
        local r,f='',(b:find(x)-1)
        for i=6,1,-1 do r=r..(f%2^i-f%2^(i-1)>0 and '1' or '0') end
        return r;
    end):gsub('%d%d%d?%d?%d?%d?%d?%d?', function(x)
        if (#x ~= 8) then return '' end
        local c=0
        for i=1,8 do c=c+(x:sub(i,i)=='1' and 2^(8-i) or 0) end
        return string.char(c)
    end))
end

-- By Phrogz https://stackoverflow.com/questions/18694131/how-to-convert-utf8-byte-arrays-to-string-in-lua
local function utf8(decimal)
	local bytemarkers = { {0x7FF,192}, {0xFFFF,224}, {0x1FFFFF,240} }
	if decimal<128 then return string.char(decimal) end
	local charbytes = {}
	for bytes,vals in ipairs(bytemarkers) do
		if decimal<=vals[1] then
		for b=bytes+1,2,-1 do
			local mod = decimal%64
			decimal = (decimal-mod)/64
			charbytes[b] = string.char(128+mod)
		end
		charbytes[1] = string.char(vals[2]+decimal)
		break
		end
	end
	return table.concat(charbytes)
end



local b64test='eJzty8sNgDAMBNGG1hIO5NfbFo+hg9znOpqXTfejPjyX9qXI5qgQfSjmclTLb3GFf3EiEAgEAoFAIBAIBAKBQCAQiEPxAuQBXW0='

M.b64dec_inflate_zlib_utf8 = function(b64)
	-- DON'T USE. Currently only sends single bytes to utf8 which of course defeats the purpose
 	local bytes_gzipped=standard_b64decode(b64)
	local bytes_gunzipped={}
	local bytestream_gunzipped=function(b)
		table.insert(bytes_gunzipped,b)
	end
	M.inflate_zlib{input=bytes_gzipped, output=bytestream_gunzipped, disable_crc=true}
	--print('b64='..#b64..' dataz='..#dataz..' type='..type(dataz)..' bu'..#bytes_gunzipped)
	local char={}
	for i=1,#bu do
		ar_char[i]=utf8(bytes_gunzipped[i]) -- The bad line. Needs to send more characters
	end

end

M.b64dec_inflate_zlib_ascii = function(b64)
	local bytes_gzipped=standard_b64decode(b64)
	--print("b64="..#b64..", bytes_gzipped="..#bytes_gzipped)
	local chars_gunzipped={}
	local bytestream_gunzipped=function(b)
		table.insert(chars_gunzipped,string.char(b))
		--print(string.char(b).." "..#chars_gunzipped)
	end
	M.inflate_zlib_nocrc{input=bytes_gzipped, output=bytestream_gunzipped}
	--print("chars_gunzipped "..#chars_gunzipped)
	return table.concat(chars_gunzipped)
end

return M
