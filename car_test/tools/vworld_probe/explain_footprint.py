"""Schematic: what 'moving V-World outlines to the ground-corrected position' means. + real ortho crop of low buildings before/after."""
import json, math, pathlib, numpy as np, cv2, sys
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; plt.rcParams['font.family'] = 'Noto Sans CJK JP'; plt.rcParams['axes.unicode_minus'] = False
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch
HERE = pathlib.Path(__file__).resolve().parent
fig = plt.figure(figsize=(24, 13)); gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.05])
# 1 side view: true building vs V-World box (both vertical, V-World shifted)
ax = fig.add_subplot(gs[0, 0]); ax.axhline(0, c='k', lw=2)
ax.add_patch(Rectangle((0, 0), 10, 30, fc='#9ecae1', ec='k', lw=1.5, label='실제 건물'))
ax.add_patch(Rectangle((2.5, 0), 10, 30, fc='none', ec='r', lw=2.5, ls='--', label='V-World 외곽선으로 세운 박스'))
ax.annotate('', xy=(2.5, -2.5), xytext=(0, -2.5), arrowprops=dict(arrowstyle='<->', lw=2, color='r')); ax.text(1.25, -4.8, '2.5 m', color='r', ha='center', fontsize=14)
ax.set_xlim(-4, 17); ax.set_ylim(-7, 36); ax.set_aspect('equal'); ax.set_xlabel('남 ← → 북 (m)'); ax.set_ylabel('높이 (m)'); ax.legend(loc='upper left', fontsize=11)
ax.set_title('① 옆에서 본 모습\nV-World 박스도 바닥에서 수직으로 올라감 (모양·높이는 맞음)\n다만 바닥 외곽선이 실제보다 2.5 m 북쪽에 그려져 있음 → 박스 전체가 2.5 m 밀림', fontsize=13)
# 2 photo: why we use low buildings
ax = fig.add_subplot(gs[0, 1]); ax.axhline(0, c='k', lw=2)
ax.add_patch(Rectangle((0, 0), 6, 8, fc='#c7e9c0', ec='k')); ax.add_patch(Rectangle((14, 0), 6, 40, fc='#c7e9c0', ec='k'))
for x0, h in ((0, 8), (14, 40)):
    ax.plot([x0 + 3, x0 + 3 + h * 0.18], [h, 46], c='0.5', ls=':', lw=1)
ax.text(3, 49, '항공기 카메라', ha='center', fontsize=12); ax.plot([3, 17], [46, 46], c='0.3', lw=6, alpha=0.3)
ax.add_patch(Rectangle((0.2, -6), 6, 2.2, fc='#41ab5d', ec='k')); ax.text(3.2, -8.5, '사진 속 지붕 ≈ 바닥', ha='center', fontsize=12)
ax.add_patch(Rectangle((14, -6), 6, 2.2, fc='none', ec='k', ls='--')); ax.add_patch(Rectangle((19.5, -6), 6, 2.2, fc='#41ab5d', ec='k')); ax.text(19.5, -8.5, '사진 속 지붕이 옆으로 밀림', ha='center', fontsize=12)
ax.set_xlim(-3, 29); ax.set_ylim(-11, 52); ax.set_aspect('equal'); ax.axis('off')
ax.set_title('② 정사영상(항공사진)의 성질\n낮은 건물은 지붕이 바닥 위치에 찍힘 → 바닥 위치를 잴 수 있음\n높은 건물은 지붕이 밀려 찍힘 → 위치 측정에 쓰지 않음', fontsize=13)
# 3 top view: measure & correct
ax = fig.add_subplot(gs[0, 2])
ax.add_patch(Rectangle((0, 0), 10, 10, fc='#41ab5d', ec='k', alpha=0.8, label='사진 속 낮은 건물 지붕 (= 실제 바닥)'))
ax.add_patch(Rectangle((0, 2.5), 10, 10, fc='none', ec='r', lw=2.5, ls='--', label='V-World 외곽선 (보정 전)'))
ax.add_patch(Rectangle((0, 0), 10, 10, fc='none', ec='b', lw=2.5, label='V-World 외곽선 (남쪽으로 2.5 m 이동 후)'))
ax.add_patch(FancyArrowPatch((11.5, 12.5), (11.5, 10), arrowstyle='-|>', mutation_scale=25, lw=2.5, color='b')); ax.text(12, 11, '2.5 m', color='b', fontsize=14)
ax.set_xlim(-2, 17); ax.set_ylim(-2, 15); ax.set_aspect('equal'); ax.set_xlabel('서 ← → 동 (m)'); ax.set_ylabel('남 ← → 북 (m)'); ax.legend(loc='lower right', fontsize=10)
ax.set_title('③ 위에서 본 모습: 보정\n낮은 건물들의 외곽선을 사진 지붕에 맞추는 이동량을 잼 (남 2.5 m)\n같은 이동을 모든 건물 외곽선에 적용 → 그 위치에서 수직으로 세움', fontsize=13)
# 4-5 real crop
meta = json.load(open(HERE / 'example' / 'ortho_z19.json')); ext = meta['ext']; img = cv2.imread(str(HERE / 'example' / 'ortho_z19.png'))[:, :, ::-1]
src = open(HERE / 'example_fig.py').read(); exec(src[src.index('LAT0, LON0, HALF'):src.index('def utm_inv')])
d = json.load(open(HERE / 'example' / 'adi_bldginfo.geojson')); rings = []
for f in d['features']:
    gg = f['geometry']; polys = gg['coordinates'] if gg['type'] == 'MultiPolygon' else [gg['coordinates']]; pr = f['properties']; h = pr.get('height') or ((pr.get('grnd_flr') or 0) * 3.3 + 1.5)
    for p in polys: e_ = np.array(p[0]); rings.append((enu(e_[:, 1], e_[:, 0]), h))
s = np.array(json.load(open(HERE / 'example' / 'ortho_align.json'))['building_shift_m'])
for k, (t, sh) in enumerate([('④ 실제 예: 보정 전 (V-World 외곽선 그대로)', (0, 0)), (f'⑤ 실제 예: 보정 후 (동 {s[0]:+.2f} m, 북 {s[1]:+.2f} m 이동)', s)]):
    ax = fig.add_subplot(gs[1, k]); ax.imshow(img, extent=ext)
    for P, h in rings:
        Q = P + sh; c = 'cyan' if h <= 25 else 'magenta'; ax.plot(np.r_[Q[:, 0], Q[0, 0]], np.r_[Q[:, 1], Q[0, 1]], c=c, lw=2 if h <= 25 else 1, ls='-' if h <= 25 else '--')
    ax.set_xlim(40, 125); ax.set_ylim(-125, -40); ax.set_aspect('equal'); ax.set_title(t + '\n하늘색 = 25 m 이하 건물, 분홍 점선 = 고층', fontsize=13)
ax = fig.add_subplot(gs[1, 2]); ax.axis('off')
ax.text(0, 0.95, '정리', fontsize=18, weight='bold', va='top')
ax.text(0, 0.85, '• V-World 외곽선은 원래 "바닥 외곽선"이 맞음.\n  문제는 모양이 아니라 그려진 자리가 2~2.5 m 북쪽으로 어긋난 것.\n\n'
        '• 보정 = 외곽선 모양은 그대로 두고 자리만 옮기는 것 (tx, ty).\n  옮긴 뒤에도 박스는 그 자리 바닥에서 수직으로 세움.\n\n'
        '• 이동량은 사진 속 낮은 건물로 잼.\n  낮은 건물은 지붕 = 바닥이라 기준으로 쓸 수 있음.\n\n'
        '• 높은 건물 지붕은 사진에서 원래 밀려 보이므로\n  보정 후에도 사진 지붕과 어긋나 보이는 게 정상.\n\n'
        '• 결과: 도로(정밀도로지도)와 건물(V-World)이\n  같은 바닥 기준에 놓임.', fontsize=14, va='top', linespacing=1.5)
plt.tight_layout(); out = '/home/diglab/workspace/workspace/instant_nurec/res_wjdaksry/1106/vworld_footprint_explain.png'; plt.savefig(out, dpi=90); print(out)
