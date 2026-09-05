"""Assemble the Blender renders into six linked README image regions."""
from pathlib import Path
import json
import argparse
from PIL import Image, ImageDraw, ImageOps

script_dir=Path(__file__).resolve().parent
if (script_dir/'profile').is_dir():
    source=script_dir/'profile'
    out=script_dir.parent/'outputs'
else:
    source=script_dir.parent
    out=script_dir.parent
(out/'assets').mkdir(exist_ok=True,parents=True)
(out/'data').mkdir(exist_ok=True)
parser=argparse.ArgumentParser()
parser.add_argument('--preview',action='store_true')
args=parser.parse_args()
refined=source/('build' if args.preview else 'assets')/'refinement'

projects=[
    {
        "id": 1,
        "key": "kernelindex",
        "name": "KernelIndex",
        "repo": "KernelIndex",
        "scene": "Matachin Tower",
        "book": "The Book of the New Sun",
        "author": "Gene Wolfe",
        "x": 18.5,
        "y": 26,
        "description": "GPU kernels indexed by operation, shape, dtype, and hardware.",
        "box": [
            0,
            0,
            600,
            550
        ]
    },
    {
        "id": 2,
        "key": "b200-kernels",
        "name": "B200 kernels",
        "repo": "sol-execbench-b200-kernels",
        "scene": "The serpent portrait",
        "book": "The Book of the New Sun",
        "author": "Gene Wolfe · after Sam Weber",
        "x": 54,
        "y": 24,
        "description": "CUDA C++ and CuTe DSL kernels for SOL-ExecBench.",
        "box": [
            600,
            0,
            1200,
            550
        ]
    },
    {
        "id": 3,
        "key": "h100-estimator",
        "name": "H100 serving estimator",
        "repo": "h100-serving-estimator",
        "scene": "Combray in a cup of tea",
        "book": "In Search of Lost Time",
        "author": "Marcel Proust",
        "x": 83.5,
        "y": 32,
        "description": "GPU time per request across 91 published vLLM runs.",
        "box": [
            1200,
            0,
            1800,
            550
        ]
    },
    {
        "id": 4,
        "key": "smollm2",
        "name": "SmolLM2 conformance",
        "repo": "smollm2-cpu-conformance",
        "scene": "The shore",
        "book": "The Book of the New Sun",
        "author": "Gene Wolfe",
        "x": 14,
        "y": 78,
        "description": "CPU checks for full-sequence and KV-cache inference.",
        "box": [
            0,
            550,
            600,
            1100
        ]
    },
    {
        "id": 5,
        "key": "tensor-parallel",
        "name": "Tensor parallel reference",
        "repo": "tensor-parallel-reference",
        "scene": "The serpent at the throat",
        "book": "The Book of the New Sun",
        "author": "Gene Wolfe · after Sam Weber",
        "x": 55,
        "y": 83,
        "description": "A CPU reference for process-isolated decoder execution.",
        "box": [
            600,
            550,
            1200,
            1100
        ]
    },
    {
        "id": 6,
        "key": "flashinfer",
        "name": "FlashInfer",
        "repo": "flashinfer",
        "scene": "The courtyard of the Casa",
        "book": "The Obscene Bird of Night",
        "author": "José Donoso",
        "x": 82,
        "y": 76,
        "description": "My fork of FlashInfer.",
        "box": [
            1200,
            550,
            1800,
            1100
        ]
    }
]
for p in projects:
    p['url']='https://github.com/SamMausberg/'+p['repo']
    p['tile']=f'assets/project-{p["id"]:02}.jpg'

atlas=Image.new('RGB',(1800,1100),'#101e27')
for name,pos in [('matachin',(0,0)),('shore',(0,550)),('combray',(1200,0)),('casa',(1200,550))]:
    candidates=[refined/f'{name}.png',source/'assets'/f'{name}-panel.png',source/'build'/f'{name}-panel-preview.png']
    path=next((p for p in candidates if p.exists()),None)
    if path is None:raise FileNotFoundError(name+' panel is not rendered yet')
    im=Image.open(path).convert('RGB')
    atlas.paste(ImageOps.fit(im,(600,550),Image.Resampling.LANCZOS),pos)
portrait_path=refined/'serpent.png'
if not portrait_path.exists():portrait_path=source/'assets/serpent-portrait.png'
portrait=Image.open(portrait_path).convert('RGB')
atlas.paste(ImageOps.fit(portrait,(600,1100),Image.Resampling.LANCZOS,centering=(.50,.5)),(600,0))

# Fine rules separate the scenes; the portrait stays continuous through the center.
d=ImageDraw.Draw(atlas)
for x in (599,1199):d.line((x,0,x,1100),fill='#14202a',width=3)
for a,b in ((0,599),(1200,1799)):d.line((a,549,b,549),fill='#14202a',width=3)
atlas.save(out/'assets/literary-atlas-clean.jpg',quality=94,subsampling=0,optimize=True)
# The artwork stays unlabelled; the README's image anchors supply the project links.
atlas.save(out/'assets/literary-atlas.jpg',quality=94,subsampling=0,optimize=True)
for p in projects:atlas.crop(p['box']).save(out/p['tile'],quality=94,subsampling=0,optimize=True)
(out/'data/projects.json').write_text(json.dumps(projects,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Composed five Blender scenes into six clickable project tiles.')
