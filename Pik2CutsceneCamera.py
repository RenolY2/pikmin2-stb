bl_info = {
    "name": "Export Camera Cutscene for Pikmin 2",
    "author": "Yoshi2",
    "version": (1, 0, 0),
    "blender": (2, 79, 0),
    "location": "File > Export > Cutscene (.json)",
    "description": "This script allows you do export col files directly from blender. Based on Blank's obj2col",
    "warning": "Runs update function every 0.2 seconds",
    "category": "Import-Export"
}
import random
import bpy
import bmesh
import threading
import json 
from bpy.types import PropertyGroup, Panel, Scene, Operator
from bpy.utils import register_class, unregister_class
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ExportHelper
from bpy.props import (BoolProperty,
    FloatProperty,
    StringProperty,
    EnumProperty, 
    IntProperty,
    PointerProperty,
    )

def jfvb_make_constant(val, index=None):
    entry = {
        "entrytype": 2, 
        "subentries": [
            {"subentry_type": "0x1",
            "subentry_data": val}
        ]
    }
    if index is not None:
        entry["fvb index"] = index 
    
    return entry

def setup_hermite(total_duration):
    subentry_range = {"subentry_type": "0x12", "subentry_data": [0.0, total_duration]}
    table = {"subentry_type": "0x1", "subentry_data": []}
    hermite = {"entrytype": 6, "subentries": [subentry_range, table]}
    
    return hermite, table["subentry_data"]
    
    
class ExportCutscene(Operator, ExportHelper): #Operator that exports the collision model into .col file
    """Save a COL file"""
    bl_idname = "export_cutscene.json"
    bl_label = "Export P2 Cutscene"
    filter_glob = StringProperty( 
        default="*.json",
        options={'HIDDEN'},
    )#This property filters what you see in the file browser to just .col files

    check_extension = True
    filename_ext = ".json" #This is the extension that the model will have
	
	#To do: add material presets
    
    fieldofview = FloatProperty(
        name="Camera FoV",
        description="Field of View",
        default=38.279388427734375,
    )
    cameraroll = FloatProperty(
        name="Camera Roll",
        description="Rotates the camera around the direction into which it looks",
        default=0.0,
    )
    framespersecond = FloatProperty(
        name="FPS",
        description="Frames per second",
        default=30.0,
    )
	
    def execute(self, context):        # execute() is called by blender when running the operator.
        #for Obj in bpy.context.scene.objects: #for all objects
        #    bpy.ops.object.mode_set(mode = 'OBJECT')#Set mode to be object mode
        #    if Obj.type != 'MESH':
        #        continue
                
        camera = target = origin = None 
        
        for obj in context.scene.objects:
            if obj.name == "P2Cutscene_Cam":
                camera = obj
                print("camera found")
            elif obj.name == "P2Cutscene_Target":
                target = obj
                print("target found")
            elif obj.name == "P2Cutscene_Origin":
                origin = obj 
                print("origin found")
        
        if camera is not None:
            print(camera.location)
        else:
            raise RuntimeError("No P2Cutscene_Cam object found!")
        if target is not None:
            print(target.location)
        else:
            raise RuntimeError("No P2Cutscene_Target object found!")
        if origin is not None:
            print(origin.location)
            offsetx = origin.location[0]
            offsety = origin.location[2]
            offsetz = -origin.location[1]
        else:
            raise RuntimeError("No P2Cutscene_Origin object found!")
        
        print(camera.animation_data)
        print(camera.animation_data.action.frame_range)
        
        framecount = context.scene.frame_end # max(camera.animation_data.action.frame_range[1], 
        
        print(camera.animation_data.action.fcurves)
        for x in camera.animation_data.action.fcurves:
            print(x)
            for y in x.keyframe_points:
                print(y.co)    
        
        cameraobj = {
            "objecttype": "JCMR",
            "name": "camera",
            "data": [
                ["0x80", [18, 18, "0x0"], [17, 18, "0x1"], 
                    [3, 18, "0x2","0x3", "0x4"],
                    [7, 18, "0x5", "0x6", "0x7"],
                    [21, 2, 1.0, 12800.0]],
                ["0x2", int(framecount)+1]
            ]
            
        }
        
        jfvbdata = []
        jfvbdata.append(jfvb_make_constant(self.fieldofview, index=0))
        jfvbdata.append(jfvb_make_constant(self.cameraroll, index=1))
        
        index = 2
        for obj in (camera, target):
            if (obj.animation_data is None 
                or obj.animation_data.action is None 
                or obj.animation_data.action.fcurves is None 
                or len(obj.animation_data.action.fcurves) == 0):
                # X
                hermite_entry, table = setup_hermite(framecount/self.framespersecond)
                hermite_entry["fvb index"] = index 
                index += 1
                
                table.append(0.0)
                table.append(obj.location[0]-offsetx)
                table.append(0.0) # Todo: bezier to hermite conversion?
                
                jfvbdata.append(hermite_entry)
                
                # Y, rotate axis
                hermite_entry, table = setup_hermite(framecount/self.framespersecond)
                hermite_entry["fvb index"] = index 
                index += 1

                table.append(0.0)
                table.append(obj.location[2]-offsety)
                table.append(0.0) # Todo: bezier to hermite conversion?
                
                jfvbdata.append(hermite_entry)
                
                # Z, rotate axis
                hermite_entry, table = setup_hermite(framecount/self.framespersecond)
                hermite_entry["fvb index"] = index 
                index += 1

                table.append(0.0)
                table.append(-obj.location[1]-offsetz)
                table.append(0.0) # Todo: bezier to hermite conversion?
                
                jfvbdata.append(hermite_entry)
            else:
                # X
                hermite_entry, table = setup_hermite(framecount/self.framespersecond)
                hermite_entry["fvb index"] = index 
                index += 1
                for x in obj.animation_data.action.fcurves[0].keyframe_points:
                    table.append(x.co[0]/self.framespersecond)
                    table.append(x.co[1]-offsetx)
                    #table.append(x.amplitude) # Todo: bezier to hermite conversion?
                    #print("x",x.co[0], x.amplitude, x.back, x.handle_left, x.handle_right, x.period)
                    diff_val = x.handle_right[1] - x.co[1]
                    diff_time = x.handle_right[0] - x.co[0]
                    
                    x.handle_left[1] = x.co[1] - diff_val 
                    x.handle_left[0] = x.co[0] - diff_time
                    
                    tangent = diff_val / ((diff_time)/self.framespersecond) 
                    table.append(tangent)
                    
                
                jfvbdata.append(hermite_entry)
                
                # Y, rotate axis
                hermite_entry, table = setup_hermite(framecount/self.framespersecond)
                hermite_entry["fvb index"] = index 
                index += 1
                for z in obj.animation_data.action.fcurves[2].keyframe_points:
                    y = z
                    table.append(y.co[0]/self.framespersecond)
                    table.append(y.co[1]-offsety)
                    #table.append(y.amplitude) # Todo: bezier to hermite conversion?
                    #print("y",y.co[0], y.amplitude, y.back, y.handle_left, y.handle_right, y.period)
                    diff_val = y.handle_right[1] - y.co[1]
                    diff_time = y.handle_right[0] - y.co[0]
                    
                    y.handle_left[1] = y.co[1] - diff_val 
                    y.handle_left[0] = y.co[0] - diff_time
                    
                    tangent = 3*diff_val / ((diff_time)/self.framespersecond) 
                    table.append(tangent)
                    
                    
                
                jfvbdata.append(hermite_entry)
                
                # Z, rotate axis
                hermite_entry, table = setup_hermite(framecount/self.framespersecond)
                hermite_entry["fvb index"] = index 
                index += 1
                for y in obj.animation_data.action.fcurves[1].keyframe_points:
                    z = y
                    table.append(z.co[0]/self.framespersecond)
                    table.append(-z.co[1]-offsetz)
                    #table.append(z.amplitude) # Todo: bezier to hermite conversion?
                    #print("z",z.co[0], z.amplitude, z.back, z.handle_left, z.handle_right, z.period)
                    diff_val = z.handle_right[1] - z.co[1]
                    diff_time = z.handle_right[0] - z.co[0]
                    
                    z.handle_left[1] = z.co[1] - diff_val 
                    z.handle_left[0] = z.co[0] - diff_time
                    
                    tangent = -diff_val / ((diff_time)/self.framespersecond)
                    print(z.handle_right,  z.co)
                    table.append(tangent)
                jfvbdata.append(hermite_entry)
        
        
        stb = [
        {"objecttype": "JFVB",
        "data": jfvbdata}, 
        cameraobj]
        
        path = self.filepath 
        
        with open(path, "w") as f:
            json.dump(stb, f, indent=" "*4)
        
        return {'FINISHED'}            # this lets blender know the operator finished successfully.
"""
class CollisionProperties(PropertyGroup): #This defines the UI elements
    ColType = IntProperty(name = "Collision type",default=0, min=0, max=65535) #Here we put parameters for the UI elements and point to the Update functions
    TerrainType = IntProperty(name = "Sound",default=0, min=0, max=255)
    UnknownField = IntProperty(name = "Unknown",default=0, min=0, max=255)#I probably should have made these an array
    HasColParameterField = BoolProperty(name="Has Parameter", default=False)
    ColParameterField = IntProperty(name = "Parameter",default=0, min=0, max=65535)

class CollisionPanel(Panel): #This panel houses the UI elements defined in the CollisionProperties
    bl_label = "Edit Collision Values"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
 
    @classmethod
    def poll(cls, context):#stolen from blender
        mat = context.material
        engine = context.scene.render.engine
        return check_material(mat) and (mat.type in {'SURFACE', 'WIRE'})
    
    def draw(self, context):
        mat = context.material.ColEditor
        column1 = self.layout.column(align = True)
        column1.prop(mat,"ColType")
        column1.prop(mat,"TerrainType")
        column1.prop(mat,"UnknownField")
        
        column1.prop(mat,"HasColParameterField")
        column2 = self.layout.column(align = True)
        column2.prop(mat,"ColParameterField")
        column2.enabled = mat.HasColParameterField #must have "Has ColParameter" checked"""
        
    
#classes = (ExportCOL,ImportCOL, CollisionPanel,CollisionProperties) #list of classes to register/unregister  
classes = (ExportCutscene, )
def register():
    for i in classes:
        register_class(i)
    #bpy.types.Material.ColEditor = PointerProperty(type=CollisionProperties) #store in the scene
    bpy.types.INFO_MT_file_export.append(menu_export) #Add to export menu
    #bpy.types.INFO_MT_file_import.append(menu_import) #Add to import menu
    

def menu_export(self, context):
    self.layout.operator(ExportCutscene.bl_idname, text="Cutscene (.json)")
    
def unregister():
    for i in classes:
        unregister_class(i)
    bpy.types.INFO_MT_file_export.remove(menu_export)

    

# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
    register()