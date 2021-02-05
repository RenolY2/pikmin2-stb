from struct import pack 

def write_uint32(f, val):
    f.write(pack(">I", val))

def write_uint16(f, val):
    f.write(pack(">H", val))

def write_float(f, val):
    f.write(pack(">f", val))

def write_padding(f, multipleof=4):
    if f.tell() % multipleof != 0:
        f.write(b"\x00"*(multipleof - f.tell() % multipleof))
    
def write_fvb(f, data):
    start = f.tell()
    f.write(b"FVB\00")
    f.write(b"\xFE\xFF\x01\x00")
    fvb_size_pos = f.tell()
    f.write(b"FBAR") # Fill in later 
    write_uint32(f, len(data)) # FVB data entries
    
    for data_entry in data:
        entry_size_pos = f.tell()
        f.write(b"FOBR")
        entry_type = data_entry["entrytype"]
        
        write_uint16(f, entry_type)
        write_uint16(f, 0x0000) # This value actually has a meaning sometimes but pikmin 2 only puts 0's here
        
        for subentry in data_entry["subentries"]:
            print(subentry)
            subtype = int(subentry["subentry_type"], 16)
            subdata = subentry["subentry_data"]
            
            if entry_type == 0x2 and subtype == 0x1: # Constant
                write_uint16(f, 0x4)
                write_uint16(f, 0x1)
                write_float(f, subdata)
                
            elif entry_type == 0x6 and subtype == 0x12: # value range 
                write_uint16(f, 0x8)
                write_uint16(f, 0x12)
                write_float(f, subdata[0])
                write_float(f, subdata[1])
                
            elif entry_type == 0x6 and subtype == 0x1: # float table 
                write_uint16(f, (len(subdata)+1)*4)
                write_uint16(f, 0x1)
                assert len(subdata) % 3 == 0
                width = 3 << 28 
                height = (len(subdata) // 3) & 0xFFFFFFF
                write_uint32(f, width | height)
                
                
                for val in subdata:
                    write_float(f, val)
            else:
                raise RuntimeError("unknown combi: {0} {1}".format(entry_type, hex(subtype)))
        
        f.write(b"\x00\x00\x00\x00")
        curr = f.tell()
        f.seek(entry_size_pos)
        write_uint32(f, curr-entry_size_pos)
        f.seek(curr)
    
    curr = f.tell()
    f.seek(fvb_size_pos)
    write_uint32(f, curr-start)
    f.seek(curr)
            
def write_cmr(f, data):
    for entry in data:
        entrytype = int(entry[0], 16)
        if entrytype == 0x2:
            framecount = entry[1]
            write_uint32(f, (entrytype << 24) | framecount)
        if entrytype >= 0x80:
            section_size_offset = f.tell()
            f.write(b"FILL")
            if len(entry) > 0:
                for paragraph in entry[1:]:
                    write_cmr_paragraph(f, paragraph)
            curr = f.tell()
            f.seek(section_size_offset)
            write_uint32(f, (0x80 << 24) | curr - section_size_offset - 4)
            f.seek(curr)
            
    write_uint32(f, 0)

def write_cmr_paragraph(f, paragraph):
    actiontype, datatype = paragraph[:2]
    
    data = paragraph[2:]
    
    combined = ((actiontype + 0x15) << 5) | datatype
    
    write_uint16(f, len(data)*4)
    write_uint16(f, combined)
    if datatype == 0x2:
        for val in data:
            write_float(f, val)
    else:
        for val in data:
            write_uint32(f, int(val, 16))
    
    
    
    
if __name__ == "__main__":
    import argparse
    import os
    import json 
    from rarc import Archive
    

    parser = argparse.ArgumentParser()
    parser.add_argument("input",
                        help="Path to json file representing the cutscene.")
    parser.add_argument("output", default=None, nargs = '?',
                        help="Output path to which the STB is written. If output points to an existing arc/szs file, write stb into archive.")

    args = parser.parse_args()
    
    if args.output is None:
        output = args.input+".stb"
    else:
        output = args.output
        
    with open(args.input, "rb") as f:
        cutscene_data = json.load(f)
    
    
    if output.endswith(".szs"):
        with open(output, "rb") as f:
            archive = Archive.from_file(f)
        out = archive["text/demo.stb" ]
        rarc = True 
    else:
        rarc = False 
        out = file.open(output, "wb")
    
    if True:
        f = out
    
        f.write(b"STB\x00")
        f.write(b"\xFE\xFF\x00\x03")
        
        stb_total_size_pos = f.tell()
        f.write(b"F00B") # Fill this in later 
        stb_obj_count_pos = f.tell()
        f.write(b"BAAR") # Same
        
        f.write(b"jstudio\x00")
        f.write(b"\x00\x00\x00\x00")
        write_uint32(f, 0x00000004)
        
        written_objects = 0
        for obj in cutscene_data:
            if obj["objecttype"] == "FFFFFFFF":
                obj["objecttype"] = "\xFF\xFF\xFF\xFF"
                
            if obj["objecttype"] not in ("JFVB", "JCMR"):
                continue 
            written_objects += 1
            section_size = f.tell()
            f.write(b"FILL")
            
            assert len(obj["objecttype"]) == 4
            f.write(bytes(obj["objecttype"], encoding="ascii"))
            
            if obj["objecttype"] == "JFVB":
                write_fvb(f, obj["data"])
            
            if obj["objecttype"] in ("JCMR", "JSND", "JACT"):
                write_uint32(f, len(obj["name"])+1)
                f.write(bytes(obj["name"], encoding="ascii"))
                f.write(b"\x00")
                write_padding(f)
            
            if obj["objecttype"] == "JCMR":
                write_cmr(f, obj["data"])
                
            
            curr = f.tell()
            f.seek(section_size)
            write_uint32(f, curr-section_size)
            f.seek(curr)
        
        total = f.tell()
        f.seek(stb_total_size_pos)
        write_uint32(f, total)
        write_uint32(f, written_objects)
    
    
    if rarc:
        with open(output, "wb") as f:
            archive.write_arc_compressed(f)
    else:
        out.close()
            