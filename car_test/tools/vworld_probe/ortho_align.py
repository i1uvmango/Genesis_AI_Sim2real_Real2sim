"""Estimate a pure translation (tx, ty) between V-World building outlines / HD lane lines and the V-World orthophoto.
Buildings: only low buildings (height <= 25 m) so roof lean in the photo is small; score = mean edge strength (Sobel on a
blurred grey image) sampled every 0.25 m along the outline. HD: lane lines (B2) scored on brightness (white paint).
Grid search tx, ty in [-8, 8] m, step 0.25 m. Writes res 1106/vworld_ortho_align.png and example/ortho_align.json."""
import json, math, pathlib, sys, numpy as np, cv2
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; plt.rcParams['font.family'] = 'Noto Sans CJK JP'; plt.rcParams['axes.unicode_minus'] = False
HERE = pathlib.Path(__file__).resolve().parent; sys.path.insert(0, '/home/diglab/workspace/workspace/ngii_hdmap'); from shp import read_shp, read_dbf
src = open(HERE / 'example_fig.py').read()
exec(src[src.index('HERE = '):src.index('# ---- V-World buildings')].replace("K = [l.split", "_K = [l.split"))   # enu, utm_inv, HD layers
meta = json.load(open(HERE / 'example' / 'ortho_z19.json')); ext = meta['ext']
img = cv2.imread(str(HERE / 'example' / 'ortho_z19.png')); H, W = img.shape[:2]; g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.2)
edge = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)); edge /= np.percentile(edge, 99)
bright = (g - np.median(g)) / (np.percentile(g, 99.5) - np.median(g))
def px(P):
    u = (P[:, 0] - ext[0]) / (ext[1] - ext[0]) * W; v = (ext[3] - P[:, 1]) / (ext[3] - ext[2]) * H; return u, v
def sample(M, P):
    u, v = px(P); ok = (u >= 0) & (u < W - 1) & (v >= 0) & (v < H - 1); return cv2.remap(M, u[ok].astype(np.float32)[None], v[ok].astype(np.float32)[None], cv2.INTER_LINEAR)[0]
def dense(rings, step=0.25):
    out = []
    for P in rings:
        for a, b in zip(P[:-1], P[1:]):
            n = max(int(np.linalg.norm(b - a) / step), 1); out.append(a + (b - a) * np.linspace(0, 1, n, endpoint=False)[:, None])
    return np.concatenate(out)
d = json.load(open(HERE / 'example' / 'adi_bldginfo.geojson')); low, high = [], []
for f in d['features']:
    gg = f['geometry']; polys = gg['coordinates'] if gg['type'] == 'MultiPolygon' else [gg['coordinates']]; pr = f['properties']
    h = pr.get('height') or ((pr.get('grnd_flr') or 0) * 3.3 + 1.5)
    for p in polys:
        e_ = np.array(p[0]); P = enu(e_[:, 1], e_[:, 0])
        if (np.abs(P) < HALF).all(1).mean() > 0.8: (low if 0 < h <= 25 else high).append(P)
print("low", len(low), "high", len(high), "lanes", len(HD["B2_SURFACELINEMARK"]), flush=True); BL = dense(low); LN = dense(HD["B2_SURFACELINEMARK"])
sh = np.arange(-8, 8.01, 0.25)
def search(Pts, M):
    S = np.array([[sample(M, Pts + [tx, ty]).mean() for tx in sh] for ty in sh]); j, i = np.unravel_index(np.argmax(S), S.shape); return S, sh[i], sh[j]
Sb, btx, bty = search(BL, edge); Sl, ltx, lty = search(LN, bright)
res = dict(low_buildings=len(low), building_shift_m=[float(btx), float(bty)], building_shift_norm=float(math.hypot(btx, bty)),
           building_score_before=float(sample(edge, BL).mean()), building_score_after=float(Sb.max()),
           hd_lane_shift_m=[float(ltx), float(lty)], hd_lane_shift_norm=float(math.hypot(ltx, lty)), hd_score_before=float(sample(bright, LN).mean()), hd_score_after=float(Sl.max()))
json.dump(res, open(HERE / 'example' / 'ortho_align.json', 'w'), indent=1); print(json.dumps(res), flush=True)
# figure: before | after (buildings shifted), zoom on low buildings + score maps
fig, axs = plt.subplots(1, 4, figsize=(30, 8), gridspec_kw=dict(width_ratios=[1, 1, 0.55, 0.55]))
for ax, (title, s) in zip(axs[:2], [('보정 전 (V-World 외곽선 그대로)', (0, 0)), (f'보정 후 (V-World 외곽선 tx {btx:+.2f} m, ty {bty:+.2f} m 이동)', (btx, bty))]):
    ax.imshow(img[:, :, ::-1], extent=ext)
    for P in low: Q = P + s; ax.plot(np.r_[Q[:, 0], Q[0, 0]], np.r_[Q[:, 1], Q[0, 1]], c='cyan', lw=1.4)
    for P in high: Q = P + s; ax.plot(np.r_[Q[:, 0], Q[0, 0]], np.r_[Q[:, 1], Q[0, 1]], c='magenta', lw=1.0, ls='--')
    for P in HD['B2_SURFACELINEMARK']: ax.plot(P[:, 0], P[:, 1], c='yellow', lw=0.7)
    ax.set_title(title + '\n하늘색 = 25 m 이하 건물(보정에 사용), 분홍 점선 = 고층(지붕 기울어짐), 노랑 = 정밀도로지도 차선', fontsize=11)
    ax.set_xlim(-HALF, HALF); ax.set_ylim(-HALF, HALF); ax.set_aspect('equal')
for ax, S, t, (x, y) in ((axs[2], Sb, 'V-World 건물 경계 점수', (btx, bty)), (axs[3], Sl, '정밀도로지도 차선 밝기 점수', (ltx, lty))):
    ax.imshow(S, extent=[sh[0], sh[-1], sh[0], sh[-1]], origin='lower', cmap='magma'); ax.plot(x, y, 'c+', ms=18, mew=2); ax.plot(0, 0, 'wo', ms=6)
    ax.set_title(f'{t}\n최대 (tx {x:+.2f}, ty {y:+.2f}) m, 흰 점 = 이동 없음', fontsize=11); ax.set_xlabel('tx 동쪽 (m)'); ax.set_ylabel('ty 북쪽 (m)')
plt.tight_layout(); out = '/home/diglab/workspace/workspace/instant_nurec/res_wjdaksry/1106/vworld_ortho_align.png'; plt.savefig(out, dpi=95); print(out)
