import struct 

def read_uint16(f):
    return struct.unpack(">H", f.read(2))[0]
    
def read_uint32(f):
    return struct.unpack(">I", f.read(4))[0]

def read_float(f):
    return struct.unpack(">f", f.read(4))[0]
    
def unpack(format, f, length):
    return struct.unpack(format, f.read(length))

def write_indented(f, indent, value, newline=True):
    f.write(" "*indent)
    f.write(value)
    if newline: 
        f.write("\n")

def read_16_32_var(f):
    val = read_uint16(f)
    val2 = read_uint16(f)
    
    if val == 0:
        val3 = read_uint32(f)
    else:
        val3 = None 
    
    return val, val2, val3
    

def write_attribute(f, indent, value, res):
    write_indented(f, indent, "\"{0}\": {1}".format(value, str(res)))
if __name__ == "__main__":
    import argparse
    import os
    import sys 
    from rarc import Archive
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("input",
                        help="Path to the archive file (usually .arc or .szs) to be extracted or the directory to be packed into an archive file.")
    parser.add_argument("output", default=None, nargs = '?',
                        help="Output path to which the archive is extracted or a new archive file is written, depending on input.")
    
    args = parser.parse_args()"""
    
    path = "D:\\Wii games\\Pikmin2ModdedFolder\\P-GPVP\\files\\user\\Mukki\\movie\\"
    datatypes = {}
    sizes = {}
    stbnum = 0
    """for dirpath, dirnames, filenames in os.walk(path):
        for file in filenames:
            if file.endswith(".szs"):
                
        #if args.input.endswith(".szs"):
                filepath = os.path.join(dirpath, file)
                with open(filepath, "rb") as g:
                    archive = Archive.from_file(g)

                f = archive["arc/demo.stb"]
            
                #with open("demo.stb", "rb") as f:
                #if True:"""
    filepath = sys.argv[1]
    with open(filepath, "rb") as f:
        with open(filepath+"_stb.json", "w") as h:
            name = f.read(4)
            assert name == b"STB\x00"
            
            bom, unknown, totalsize, objectcount = unpack(">HHII", f, 0xC)
            jstudio = f.read(8)
            #print(jstudio)
            assert jstudio == b"jstudio\00"
            pad = f.read(6)
            unknown = read_uint16(f)
            write_indented(h, 0, "[")
            
            
            for object_index in range(objectcount):
                current = f.tell()
                objectsize = read_uint32(f)
                objectname = f.read(4)
                datatypes[objectname] = True
                #print(objectname)
                write_indented(h, 4, "{")
                if objectname == b"\xFF\xFF\xFF\xFF":
                    objectname = b"FFFFFFFF"
                write_attribute(h, 8, "objecttype", "\"{0}\",".format(str(objectname, encoding="ascii", errors="backslashreplace")))
                
                
                if objectname == b"JFVB":
                    #print("FVB start")
                    fvbstart = f.tell()
                    assert f.read(4) == b"FVB\x00"
                    assert read_uint16(f) == 0xFEFF
                    assert read_uint16(f) == 0x0100
                    fvbsize = read_uint32(f)
                    fvbentrycount = read_uint32(f)
                    #print(fvbentrycount, "entries")
                    write_indented(h, 8, "\"data\": [")
                    for i in range(fvbentrycount):
                        
                        entrystart = f.tell()
                        entrysize = read_uint32(f)
                        entrytype = read_uint16(f)
                        
                        offset = read_uint16(f)
                        assert offset == 0
                        #print("entry type:", entrytype, entrysize, offset)
                        end = entrystart+entrysize 
                        
                        if entrytype not in (2,6):
                            raise RuntimeError("This is amazing: {0}".format(entrytype))
                        
                        #f.seek(entrystart)
                        write_indented(h, 12, "{")
                        write_attribute(h, 16, "entrytype", "{0},".format(entrytype))
                        write_attribute(h, 16, "fvb index", "\"0x{0:X}\",".format(i))
                        write_attribute(h, 16, "subentries", "[")
                        firstiteration = True
                        while f.tell() < end:
                            
                                
                            subentry_size, subentry_type = read_uint16(f), read_uint16(f)
                            if subentry_type not in (0, 1, 0x12):
                                raise RuntimeError("This is amazing: {0}".format(subentry_type))
                            if subentry_type == 0x12: assert entrytype == 0x6
                                
                            if subentry_size == subentry_type == 0:
                                break 
                            else:
                                if not firstiteration:
                                    write_indented(h, 20, ",")
                                else:
                                    firstiteration = False 
                            
                                start = f.tell()
                                assert subentry_size % 4 == 0
                                
                                subentry_end = start+subentry_size
                                
                                #print("subentry type", hex(subentry_type))
                                write_indented(h, 20, "{")
                                write_attribute(h, 24, "subentry_type", "\"0x{0:X}\",".format(subentry_type))
                                
                                if subentry_type == 1 and entrytype == 2:
                                    constant = read_float(f)
                                    write_attribute(h, 24, "subentry_data", str(constant))
                                elif subentry_type == 1 and entrytype == 6:
                                    dim = read_uint32(f)
                                    height = dim & 0x0FFFFFFF
                                    width = dim >> 28 
                                    assert width == 3
                                    
                                    total = width*height 
                                    
                                    write_attribute(h, 24, "subentry_data", "[")
                                    for y in range(height):
                                        h.write(" "*24)
                                        for ij in range(width):
                                            if ij > 0:
                                                h.write(", ")
                                            h.write(str(read_float(f)))
                                        if y < height-1:
                                            h.write(",")
                                        h.write("\n")
                                    write_indented(h, 24, "]")
                                    
                                elif subentry_type == 0x12:
                                    range_start = read_float(f)
                                    range_end = read_float(f)
                                    write_attribute(h, 24, "subentry_data", "[{0}, {1}]".format(range_start, range_end))
                                        
                                write_indented(h, 20, "}")
                                f.seek(subentry_end)
                                
                        write_indented(h, 16, "]")
                        
                        sep = "," if i < fvbentrycount-1 else ""
                        write_indented(h, 12, "}"+sep)
                            
                        f.seek(entrystart+entrysize)
                        
                    write_indented(h, 8, "]")
                    
                    #print("FVB end") 
                
                elif objectname in (b"JACT", b"JCMR", b"JSND"):
                    namesize = read_uint32(f)
                    name = f.read(namesize-1)
                    write_attribute(h, 8, "name", "\"{0}\",".format(str(name,encoding="ascii")))
                    
                    if True:
                        padding = 4 - f.tell()%4
                        if padding == 4: padding = 0
                        f.read(padding)
                        next = read_uint32(f)
                        
                        write_attribute(h, 8, "data", "[")
                        
                        while next != 0:
                            actiontype = next >> 24 
                            val = next & 0xFFFFFF
                            
                            if actiontype >= 0x80:
                                datasize = val 
                                end = f.tell() + datasize 
                                write_indented(h, 12, "[")
                                write_indented(h, 16, "\""+str(hex(actiontype))+"\",")
                                while f.tell() < end:
                                    val, val2, val3 = read_16_32_var(f)
                                    pad = 4 - val%4 
                                    if pad == 4: pad = 0
                                    datalen = val + pad
                                    #print(val, hex(val2), val3, objectname, filepath)
                                    assert val3 is None 
                                    
                                    #print(f.tell(), end, f.tell() < end)
                                    
                                    vallist = []
                                    vallist.append((val2 >> 5) - 0x15)
                                    vallist.append(val2 & 0b11111)
                                    if objectname == b"JCMR":
                                        assert val2 & 0b11111 in (2, 18)
                                        
                                    if val2& 0b11111 == 0x2:
                                        for i in range(datalen//4):
                                            vallist.append(str(read_float(f)))

                                    else:
                                        for i in range(datalen//4):
                                            vallist.append("\""+str(hex(read_uint32(f)))+"\"")
                                        
                                    sep = "," if  f.tell() < end else ""
                                    
                                    
                                    
                                    write_indented(h, 16, "[{0}]{1}".format(
                                        ", ".join(str(x) for x in vallist),
                                        sep)
                                        )
                                        

                                    """for i in range(3):
                                        h.write(" "*12)
                                        for j in range(4):
                                            val = read_uint32(f)
                                            if j > 0:
                                                h.write(", ")
                                            h.write(str(hex(val)))

                                        h.write("\n")
                                            
                                    write_indented(h, 12, hex(read_uint32(f)))
                                    write_indented(h, 12, str(read_float(f)))
                                    write_indented(h, 12, str(read_float(f)))
                                    write_indented(h, 12, hex(read_uint32(f)))
                                    next = read_uint32(f)"""
                                next = read_uint32(f)
                                sep = "," if next != 0 else ""
                                write_indented(h, 12, "]"+sep)
                                
                            elif actiontype == 0x02:
                                framecount = val 
                                next = read_uint32(f)
                                sep = "," if next != 0 else ""
                                write_indented(h, 12, "[\"0x{0}\", {1}]{2}".format(actiontype, framecount, sep))
                            else:
                                raise RuntimeError("Unknown")
                            
                            
                        write_indented(h, 8, "]")
                else:
                    write_attribute(h, 8, "foo", "\"bar\"")
                write_indented(h, 4, "}")
                if object_index != objectcount-1:
                    write_indented(h, 4, ",")
                f.seek(current+objectsize)
            
            write_indented(h, 0, "]")
                    
            """with open(os.path.join(dirpath, file)+"_stb.json", "rb") as h:
                outname = os.path.basename(dirpath)
                print(outname)
                with open("cameras/{0}_stb.json".format(outname), "wb") as g:
                    g.write(h.read())
            
            stbnum += 1"""
                        
    print(datatypes.keys())
    #for i, v in sizes.items():
    #    with open("cmr-{0}.bin".format(i), "wb") as cmr:
    #        cmr.write(v)
            
    
                    
                