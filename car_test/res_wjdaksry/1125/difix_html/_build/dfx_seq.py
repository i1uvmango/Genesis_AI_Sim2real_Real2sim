import sys, os, json, time
os.environ['HF_HOME'] = '/home/diglab/workspace/hf_cache'
import torch
from PIL import Image
sys.path.insert(0, '/home/diglab/workspace/workspace/instant_nurec/work/night_20261109/difix/Difix3D/src')
from pipeline_difix import DifixPipeline
H = os.path.dirname(os.path.abspath(__file__)); IN = f'{H}/out/render_seqd3'; OUT = f'{H}/out/seq_plus'; os.makedirs(OUT, exist_ok=True)
seq = json.load(open('/home/diglab/workspace/workspace/instant_nurec/results/alpamayo/058bf960/alpamayo_full_clip/video_v3/seq_left.json'))
pipe = DifixPipeline.from_pretrained('nvidia/difix_ref', trust_remote_code=True, torch_dtype=torch.float16).to('cuda'); pipe.set_progress_bar_config(disable=True)
t = time.time()
for k, r in enumerate(seq):
    im0 = Image.open(f'{IN}/{r["name"]}.jpg').convert('RGB'); im = im0.resize((1024, 384), Image.LANCZOS); ref = Image.open(r['ref']).convert('RGB').resize(im.size)
    o = pipe(prompt='remove degradation', image=im, ref_image=ref, num_inference_steps=1, timesteps=[199], guidance_scale=0.0).images[0]
    o.resize(im0.size, Image.LANCZOS).save(f'{OUT}/{r["name"]}.jpg', quality=93)
    if k % 50 == 0: print(k, round(time.time() - t, 1), flush=True)
print('done', round(time.time() - t, 1))
