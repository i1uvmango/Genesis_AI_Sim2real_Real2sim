"""Collect / convert every media file of the Difix3D+ HTML deck into 1125/difix_html/media and write media/data.js."""
import os, json, shutil, subprocess, glob
from PIL import Image
SP = '/home/diglab/workspace/tmp/claude-1000/-home-diglab-workspace-workspace-genesis-doc/05d4948b-aae4-4d1d-94eb-7ef1a96b14b6/scratchpad'
RES = '/home/diglab/workspace/workspace/genesis-doc/car_test/res_wjdaksry'; PP = f'{RES}/1124/difix_ppt'; PAP = f'{PP}/paper'; SEM = f'{RES}/1121/seminar'
H = f'{RES}/1125/difix_html'; M = f'{H}/media'
IMG = '/home/diglab/workspace/workspace/instant_nurec/work/pai058_20261107/images'; ADI = '/home/diglab/workspace/workspace/instant_nurec/work/seq60_20261105/images'
K = '/home/diglab/workspace/workspace/instant_nurec/results/adi/seq60/scene_L000-300_lidar/k1/b200'
R = f'{SP}/h/out'; C = f'{SP}/cur/out'; TD = f'{SP}/vid/td2'
def jpg(src, dst, w=None, q=84, crop=None):
    dst = f'{M}/{dst}'; os.makedirs(os.path.dirname(dst), exist_ok=True)
    im = Image.open(src).convert('RGB')
    if crop: im = im.crop(crop)
    if w and im.width > w: im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(dst, quality=q)
def mp4(src, dst, extra=''):
    dst = f'{M}/{dst}'; subprocess.run(f'ffmpeg -y -loglevel error -i "{src}" {extra} -movflags +faststart -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -c:v libx264 -crf 22 -preset slow "{dst}"', shell=True, check=True)
D = {}
# paper figures
for n in ('fig4_tau', 'fig5_inthewild', 'fig6_rds', 'fig7_post', 'fig8_ablation', 'tab1_curation', 'tab4_ablation', 'tab5_difix'): jpg(f'{PAP}/{n}.png', f'{n}.jpg', w=2200, q=90)
jpg(f'{SEM}/paper_fig2_difix3d_pipeline.png', 'fig2_pipeline.jpg', w=2400, q=90); jpg(f'{SEM}/paper_fig3_difix_architecture.png', 'fig3_arch.jpg', w=2200, q=90)
jpg(f'{SEM}/sdturbo_train.png', 'sdturbo_train.jpg', q=92)
# videos from gifs
mp4(f'{PP}/alpamayo_3dgs_build.gif', 'build.mp4'); mp4(f'{PP}/difix3d_pseudo_view_alpamayo.gif', 'pseudo_view.mp4')
# s3 viewer + s14 wipe
for L in (60, 120):
    jpg(f'{IMG}/front_{L:04d}.jpg', f's3/real_{L:03d}.jpg', w=1200, q=82)
    for o in range(16):
        for y in range(7): jpg(f'{R}/render_viewer/v{L:03d}_o{o:02d}_y{y}.jpg', f's3/v{L:03d}_o{o:02d}_y{y}.jpg', w=1200, q=80)
        jpg(f'{R}/render_viewerD3/v{L:03d}_o{o:02d}_y0.jpg', f's14/d3_{L:03d}_o{o:02d}.jpg', w=1200, q=82)
# s7 reference animation
cams = json.load(open(f'{TD}/cams.json'))
jpg(f'{TD}/bg_final.png', 's7/top.jpg', q=85)
for p in cams['pseudo']:
    k = p['key']; jpg(f'{TD}/under_pseudo/{k}.png', f's7/nv_{k}.jpg', w=960, q=82); jpg(f'{TD}/difix_pseudo/{k}.png', f's7/fx_{k}.jpg', w=960, q=82)
    jpg(f'{IMG}/{p["ref"]}.jpg', f's7/ref_{p["ref"]}.jpg', w=960, q=82)
D["s7"] = dict(W=cams["W"], H=cams["H"], path=cams["path"], pseudo=cams["pseudo"], real=cams["real"])
# s8: cycle (labels 40-79), cross (42-78 even), under (40-79)
for l in range(40, 80):
    for d in ('front', 'left', 'right'): jpg(f'{IMG}/{d}_{l:04d}.jpg', f's8/gt_{d}_{l:04d}.jpg', w=960, q=80)
    jpg(f'{C}/render_cycA/cyc_f{l:04d}_front.jpg', f's8/cycA_{l:04d}.jpg', w=960, q=80)
    jpg(f'{C}/snap_cycB/it03000_front_{l:04d}.jpg', f's8/cycB_{l:04d}.jpg', w=960, q=80)
    for d in ('front', 'left', 'right'): jpg(f'{R}/render_under1k/{d}_{l:04d}.jpg', f's8/under_{d}_{l:04d}.jpg', w=960, q=80)
    if l % 2 == 0 and l >= 42:
        for d in ('left', 'right'): jpg(f'{C}/snap_cross/it03000_{d}_{l:04d}.jpg', f's8/cross_{d}_{l:04d}.jpg', w=960, q=80)
for it in range(0, 3001, 100): jpg(f'{C}/snap_under/it{it:05d}_front_0060.jpg', f's8/uit_{it:05d}.jpg', w=960, q=80)
for n in ('cycle', 'cross', 'under'): shutil.copy(f'{M}/figS2_{n}.jpg', f'{M}/s8/figS2_{n}.jpg') if os.path.exists(f'{M}/figS2_{n}.jpg') else None
# s11: ADI b200 progressive steps
for s in range(1, 15):
    for v in ('chase', 'laneL_fwd', 'laneLL_fwd'): jpg(f'{K}/step_k1c/{s:02d}/st_{v}_0220.jpg', f's11/{v}_{s:02d}.jpg', w=1200, q=82)
for d in ('front', 'rear'): jpg(f'{ADI}/{d}_0220.jpg', f's11/real_{d}_0220.jpg', w=1200, q=82)
# s12: Difix3D vs Difix3D+ drive, side by side 2880x540
os.makedirs(f'{SP}/h/sbs', exist_ok=True)
for f in sorted(glob.glob(f'{R}/render_seqd3/*.jpg')):
    n = os.path.basename(f); a = Image.open(f).convert('RGB'); b = Image.open(f'{R}/seq_plus/{n}').convert('RGB')
    cv = Image.new('RGB', (a.width * 2, a.height)); cv.paste(a, (0, 0)); cv.paste(b, (a.width, 0)); cv.save(f'{SP}/h/sbs/{n}', quality=92)
subprocess.run(f'ffmpeg -y -loglevel error -framerate 12 -pattern_type glob -i "{SP}/h/sbs/lf_f*.jpg" -movflags +faststart -pix_fmt yuv420p -c:v libx264 -crf 21 -preset slow {M}/drive_d3_vs_plus.mp4', shell=True, check=True)
# s14 ADI
for k in ('before', 'after', 'gt'): jpg(f'{RES}/1116/difix_s60_rear_0025_{k}.jpg', f's14/adi_{k}.jpg', q=90)
# s15 hallucination row 2
jpg(f'{RES}/1116/r_difix_hallucination.png', 'halluc_row2.jpg', q=90, crop=(0, 500, 2212, 985))
json.dump(D, open(f'{M}/data.json', 'w'))
open(f'{M}/data.js', 'w').write('window.DECK=' + json.dumps(D) + ';')
print('ok')
