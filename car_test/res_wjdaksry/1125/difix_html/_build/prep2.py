"""11/25 round 2 of the HTML deck media: full-width build video (s2), full Fig 2 (s5), hi-res zoom sources (s9), k5 b040 progressive steps (s11),
ADI Difix distillation tiles + Alpamayo safecd_0589 sweep (s14), Alpamayo limitation stills (s15). CPU only (k8 training owns the GPU)."""
import os, json, subprocess
from PIL import Image
SP = '/home/diglab/workspace/tmp/claude-1000/-home-diglab-workspace-workspace-genesis-doc/05d4948b-aae4-4d1d-94eb-7ef1a96b14b6/scratchpad'
RES = '/home/diglab/workspace/workspace/genesis-doc/car_test/res_wjdaksry'; M = f'{RES}/1125/difix_html/media'; PA = f'{SP}/paper'
K5 = '/home/diglab/workspace/workspace/instant_nurec/results/adi/seq60/scene_L000-300_lidar/k1/k5out/b040/step_k5'
ADI = '/home/diglab/workspace/workspace/instant_nurec/work/seq60_20261105/images'; IMG = '/home/diglab/workspace/workspace/instant_nurec/work/pai058_20261107/images'
AM = '/home/diglab/workspace/workspace/instant_nurec/shm_backup_20261123/alpamayo_v3/model'; HO = f'{SP}/h/out'
def save(im, dst, w=None, q=86):
    dst = f'{M}/{dst}'; os.makedirs(os.path.dirname(dst), exist_ok=True); im = im.convert('RGB')
    if w and im.width > w: im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(dst, quality=q) if dst.endswith('.jpg') else im.save(dst)
O = lambda p: Image.open(p)
# s2: full 1920-wide render band of the build segment
subprocess.run(f'ffmpeg -y -loglevel error -ss 4.3 -t 5.5 -i {RES}/1121/seminar/difix3d_pseudo_view_alpamayo.mp4 -vf "crop=1920:720:0:150,scale=1440:540:flags=lanczos" '
               f'-movflags +faststart -pix_fmt yuv420p -c:v libx264 -crf 20 -preset slow -an {M}/build_full.mp4', shell=True, check=True)
# s5: Fig 2 with its legend (page 2 at 600 dpi)
save(O(f'{PA}/r600-02.png').crop((520, 580, 4600, 2392)), 'fig2_full.jpg', w=2600, q=90)
# s9: zoom sources -- embedded Fig 3 photos (native) and vector blocks from the 600-dpi page
p5 = O(f'{PA}/r600-05.png')
for k, n in (('input', 0), ('ref', 1), ('output', 2), ('refout', 3)):
    im = O(f'{PA}/p5img/im-{n:03d}.png').convert('RGBA'); bg = Image.new('RGBA', im.size, 'white'); save(Image.alpha_composite(bg, im), f's9/{k}.png')
for k, (x0, y0, x1, y1) in dict(enc=(248, 120, 309, 246), unet=(312, 118, 398, 238), mix=(396, 100, 526, 244), zero=(318, 238, 420, 282), dec=(524, 112, 597, 220)).items():
    save(p5.crop((x0 * 6, y0 * 6, x1 * 6, y1 * 6)), f's9/{k}.png')
save(O(f'{RES}/1121/seminar/sdturbo_train.png').crop((1900, 540, 2110, 735)), 's9/loss.png')
# s11: k5 block 40, 14 Difix steps (every 2,000 it of 30,000)
for s in range(1, 15):
    for v in ('chase', 'laneL_fwd', 'laneLL_fwd'): save(O(f'{K5}/{s:02d}/st_{v}_0060.jpg'), f's11b/{v}_{s:02d}.jpg', w=1200, q=84)
save(O(f'{ADI}/front_0060.jpg'), 's11b/real_front_0060.jpg', w=900, q=84)
# s14 ADI: 1115 Difix distillation figure, 4 views x (before, after)
f = O(f'{RES}/1115/difix_before_after.png').convert('RGB')
rows = [(60, 330), (338, 607), (616, 885), (894, 1163)]
for i, (y0, y1) in enumerate(rows):
    save(f.crop((0, y0 + 38, 720, y1)), f's14b/adi_v{i}_before.jpg', q=90); save(f.crop((728, y0 + 38, 1448, y1)), f's14b/adi_v{i}_after.jpg', q=90)
# s14 Alpamayo: safecd_0589 chase-camera sideways sweep, every 3rd frame
sw = json.load(open('/home/diglab/workspace/workspace/instant_nurec/results/alpamayo/058bf960/alpamayo_full_clip/video_v3/sweep_safe_cd_0589.json'))
offs = []
for i in range(0, len(sw), 3):
    n = sw[i]['name']; offs.append(round(sw[i]['offset'], 2))
    for t in ('before', 'after'): save(O(f'{AM}/render_safecd_0589_{t}/{n}.jpg'), f's14b/alp_{t}_{i // 3:03d}.jpg', w=1200, q=82)
json.dump(offs, open(f'{M}/s14b/alp_offsets.json', 'w'))
# s15: Alpamayo limitation -- frame-wise inconsistent Difix3D+ cars, and the poster painted into the 3D
for fr in (196, 204, 212, 220):
    save(O(f'{HO}/render_seqd3/lf_f{fr:04d}.jpg'), f's15/d3_{fr}.jpg', w=960, q=84); save(O(f'{HO}/seq_plus/lf_f{fr:04d}.jpg'), f's15/plus_{fr}.jpg', w=960, q=84)
save(O(f'{IMG}/front_0150.jpg'), 's15/ref_0150.jpg', w=960, q=84)
pp = O(f'{RES}/1116/r_pai_progress_steps.png').convert('RGB')
for k, box in dict(gt=(0, 179, 641, 457), fix1=(1423, 639, 2063, 917), st4=(3557, 179, 4190, 457)).items(): save(pp.crop(box), f's15/poster_{k}.jpg', q=90)
print('offsets', offs[:5], len(offs))
