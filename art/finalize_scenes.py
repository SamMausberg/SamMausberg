"""Reframe the approved studies into the four side panels of the profile."""
from pathlib import Path
import argparse
import sys
import bpy
from mathutils import Vector

script_dir=Path(__file__).resolve().parent
root=script_dir/'profile' if (script_dir/'profile').is_dir() else script_dir.parent
p=argparse.ArgumentParser()
p.add_argument('--preview',action='store_true')
p.add_argument('--scenes',nargs='+',default=['matachin','shore','combray','casa'])
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
for name in a.scenes:
    bpy.ops.wm.open_mainfile(filepath=str(root/'build'/f'{name}.blend'))
    s=bpy.context.scene
    s.render.resolution_x=1000
    s.render.resolution_y=917
    s.render.resolution_percentage=50 if a.preview else 100
    s.cycles.samples=22 if a.preview else 32
    s.render.threads=8
    s.camera.data.ortho_scale={'matachin':19.0,'shore':16.0,'combray':6.7,'casa':11.5}[name]
    if name=='shore':
        c=s.camera
        c.location=(7,-21,6)
        c.rotation_euler=(Vector((0,0,1.3))-c.location).to_track_quat('-Z','Y').to_euler()
        c.location+=c.rotation_euler.to_matrix()@Vector((0,0,40))
        bpy.data.objects['Beach'].scale.x*=5
        bpy.data.objects['Beach'].scale.y*=5
        sun=bpy.data.objects['Last red sun']
        sun.location=(-7,25,1.8)
        sun.scale.x=1.3/1.9
        sun.scale.y=1.3/1.9
        sun.rotation_euler=c.rotation_euler
        old=[o for o in list(s.objects) if o.name.startswith('Thin breaking wave')]
        for i,o in enumerate(old):
            if i%2==1:bpy.data.objects.remove(o,do_unlink=True)
    s.render.filepath=str(root/('build' if a.preview else 'assets')/(name+'-panel-preview.png' if a.preview else name+'-panel.png'))
    if not a.preview:bpy.ops.wm.save_as_mainfile(filepath=str(root/'build'/f'{name}-panel.blend'),compress=True)
    bpy.ops.render.render(write_still=True)
