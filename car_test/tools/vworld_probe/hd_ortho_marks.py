"""HD map (SEC008) vs V-World orthophoto, ground features only: lane lines (B2) + surface marks (B3: crosswalk bars, arrows,
stop lines) rasterised as a mask, correlated with the photo's white paint (brightness above local median). Translation grid
search +-6 m, 0.1 m step. Writes example/hd_ortho_marks.json and res 1106/hd_ortho_marks.png"""
import json, math, pathlib, sys, numpy as np, cv2
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; plt.rcParams['font.family'] = 'Noto Sans CJK JP'; plt.rcParams['axes.unicode_minus'] = False
HERE = pathlib.Path(__file__).resolve().parent; sys.path.insert(0, '/home/diglab/workspace/workspace/ngii_hdmap'); from shp import read_shp, read_dbf
src = open(HERE / 'example_fig.py').read(); exec(src[src.index('HERE = '):src.index('# ---- V-World buildings')].replace("K = [l.split", "_K = [l.split"))
meta = json.load(open(HERE / 'example' / 'ortho_z19.json')); ext = meta['ext']
img = cv2.imread(str(HERE / 'example' / 'ortho_z19.png')); H, W = img.shape[:2]; mpp = (ext[1] - ext[0]) / W
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32); loc = cv2.medianBlur(g.astype(np.uint8), 31).astype(np.float32)
paint = np.clip((g - loc - 15) / 40, 0, 1)                      # white paint above local road brightness
def to_px(P): return np.c_[(P[:, 0] - ext[0]) / mpp, (ext[3] - P[:, 1]) / mpp]
def raster(shift):
    m = np.zeros((H, W), np.float32)
    for P in HD['B3_SURFACEMARK']: cv2.fillPoly(m, [np.round(to_px(P + shift) * 4).astype(np.int32)], 1.0, shift=2)
    for P in HD['B2_SURFACELINEMARK']: cv2.polylines(m, [np.round(to_px(P + shift) * 4).astype(np.int32)], False, 1.0, thickness=2, shift=2)
    return m
road = np.zeros((H, W), np.uint8)                                  # evaluate only near the HD road (within 25 m of lane links)
for P in HD['A2_LINK']: cv2.polylines(road, [np.round(to_px(P)).astype(np.int32)], False, 1, thickness=int(2 * 25 / mpp))
sh = np.arange(-6, 6.01, 0.2); S = np.zeros((len(sh), len(sh)))
for j, ty in enumerate(sh):
    for i, tx in enumerate(sh):
        m = raster(np.array([tx, ty])); S[j, i] = (m * paint * road).sum() / max((m * road).sum(), 1)
j, i = np.unravel_index(np.argmax(S), S.shape); bx, by = sh[i], sh[j]; s0 = S[len(sh) // 2, len(sh) // 2]
# along / across the road (road direction from lane links)
L = np.concatenate([np.diff(P, axis=0) for P in HD['A2_LINK']]); ang = np.arctan2(L[:, 1], L[:, 0]); ang = np.where(ang < 0, ang + np.pi, ang)
fw = np.array([math.cos(np.median(ang)), math.sin(np.median(ang))]); rt = np.array([-fw[1], fw[0]])
res = dict(best_shift_east_north_m=[float(bx), float(by)], along_road_m=float(np.dot([bx, by], fw)), across_road_m=float(np.dot([bx, by], rt)),
           score_no_shift=float(s0), score_best=float(S.max()), road_dir_deg_from_east=float(math.degrees(math.atan2(fw[1], fw[0]))))
json.dump(res, open(HERE / 'example' / 'hd_ortho_marks.json', 'w'), indent=1); print(json.dumps(res), flush=True)
fig, axs = plt.subplots(1, 3, figsize=(26, 9), gridspec_kw=dict(width_ratios=[1, 1, 0.6]))
for ax, (t, s) in zip(axs[:2], [('보정 전 (정밀도로지도 그대로)', (0, 0)), (f'보정 후 (동 {bx:+.1f} m, 북 {by:+.1f} m 이동)', (bx, by))]):
    ax.imshow(img[:, :, ::-1], extent=ext)
    for P in HD['B3_SURFACEMARK']: Q = P + s; ax.fill(Q[:, 0], Q[:, 1], fc='none', ec='red', lw=1.0)
    for P in HD['B2_SURFACELINEMARK']: Q = P + s; ax.plot(Q[:, 0], Q[:, 1], c='yellow', lw=0.8)
    ax.set_xlim(-40, 70); ax.set_ylim(-110, 0); ax.set_aspect('equal'); ax.set_title(t + '\n빨강 = 노면표시(횡단보도·화살표), 노랑 = 차선 (정밀도로지도)', fontsize=12)
axs[2].imshow(S, extent=[sh[0], sh[-1], sh[0], sh[-1]], origin='lower', cmap='magma'); axs[2].plot(bx, by, 'c+', ms=18, mew=2); axs[2].plot(0, 0, 'wo', ms=6)
axs[2].set_title(f'흰 페인트 겹침 점수\n최대 (동 {bx:+.1f}, 북 {by:+.1f}) m = 도로 방향 {res["along_road_m"]:+.1f} m, 가로 {res["across_road_m"]:+.1f} m', fontsize=12); axs[2].set_xlabel('동쪽 이동 (m)'); axs[2].set_ylabel('북쪽 이동 (m)')
plt.tight_layout(); out = '/home/diglab/workspace/workspace/instant_nurec/res_wjdaksry/1106/hd_ortho_marks.png'; plt.savefig(out, dpi=95); print(out)
