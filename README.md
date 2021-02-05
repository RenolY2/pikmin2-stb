# pikmin2-stb
Collection of tools relating to Pikmin 2 stb (cutscene) files. Unfinished, experimental. Use at your own risk. Useful for research into Pikmin 2 stb files.

# dumpstb.py
Dumps an stb file into json format

# makestb.py 
Turns a json file into a stb file again.

# Pik2CutsceneCamera.py
Blender plugin for creating camera cutscenes. It exports a json that can be turned to stb with makestb.
Three objects are used by this plugin that you need to create, named P2Cutscene_Cam, P2Cutscene_Target and P2Cutscene_Origin.
They can be any kind of object, e.g. a cube.

P2Cutscene_Origin represents the origin of the cutscene, similar to the origin parameter of cutscenes in Pikmin 2.
P2Cutscene_Cam represents the position of the viewer and P2Cutscene_Target represents the point being looked at.
By animating the positions of P2Cutscene_Cam and P2Cutscene_Target you can create camera animations.
