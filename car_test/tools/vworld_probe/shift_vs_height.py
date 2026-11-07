"""Per-building shift of V-World outlines vs the orthophoto, as a function of building height (route area).
If the shift is the same for all heights -> outline position error; if it grows with height -> photo relief (lean)."""
import json, math, pathlib, numpy as np, cv2
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; plt.rcParams['font.family'] = 'Noto Sans CJK JP'; plt.rcParams['axes.unicode_minus'] = False
W = pathlib.Path('/home/diglab/Documents/ChatGPT/3DGS mesh/work/seq60_20261105/vworld'); osm = json.load(open(W.parent / 'osm_to_world.json')); LAT0, LON0 = osm['lat0'], osm['lon0']; Rr = 6378137.0
def enu(lat, lon): return np.c_[np.radians(lon - LON0) * Rr * math.cos(math.radians(LAT0)), np.radians(lat - LAT0) * Rr]
ext = json.load(open(W / 'route_ortho_z19.json'))['ext']; img = cv2.imread(str(W / 'route_ortho_z19.png')); H, Wd = img.shape[:2]; mpp = (ext[1] - ext[0]) / Wd
g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.2); edge = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)); edge /= np.percentile(edge, 99)
def samp(P):
    p = np.c_[(P[:, 0] - ext[0]) / mpp, (ext[3] - P[:, 1]) / mpp]; ok = (p[:, 0] >= 0) & (p[:, 0] < Wd - 1) & (p[:, 1] >= 0) & (p[:, 1] < H - 1)
    return cv2.remap(edge, p[ok, 0].astype(np.float32)[None], p[ok, 1].astype(np.float32)[None], cv2.INTER_LINEAR)[0], ok.mean()
def dense(P, step=0.25):
    return np.concatenate([a + (b - a) * np.linspace(0, 1, max(int(np.linalg.norm(b - a) / step), 1), endpoint=False)[:, None] for a, b in zip(P[:-1], P[1:])])
d = json.load(open(W / 'route_bldginfo.geojson')); sh = np.arange(-6, 6.01, 0.25); rows = []
for f in d['features']:
    gg = f['geometry']; polys = gg['coordinates'] if gg['type'] == 'MultiPolygon' else [gg['coordinates']]; pr = f['properties']
    h = pr.get('height') or 0
    if h <= 0: continue
    P = enu(np.array(polys[0][0])[:, 1], np.array(polys[0][0])[:, 0]); D = dense(P)
    if len(D) < 120: continue                                    # perimeter >= 30 m
    _, cov = samp(D)
    if cov < 0.99: continue
    S = np.array([[samp(D + [tx, ty])[0].mean() for tx in sh] for ty in sh]); j, i = np.unravel_index(np.argmax(S), S.shape)
    peak = S.max() / np.median(S)                                # sharpness of the best match
    if peak < 1.4 or i in (0, len(sh) - 1) or j in (0, len(sh) - 1): continue
    rows.append((h, sh[i], sh[j], peak, pr.get('bld_nm')))
A = np.array([r[:4] for r in rows]); h, ex, ny = A[:, 0], A[:, 1], A[:, 2]
lowm = h <= 25; out = dict(n=len(rows), n_low=int(lowm.sum()))
for nm, m in (('low_le_25m', lowm), ('high_gt_25m', ~lowm)):
    if m.sum(): out[nm] = dict(n=int(m.sum()), east_median=float(np.median(ex[m])), north_median=float(np.median(ny[m])))
pe = np.polyfit(h, ex, 1); pn = np.polyfit(h, ny, 1); out.update(east_vs_height_slope_m_per_m=float(pe[0]), east_intercept=float(pe[1]), north_vs_height_slope_m_per_m=float(pn[0]), north_intercept=float(pn[1]))
json.dump(dict(out, rows=[list(map(lambda v: v if isinstance(v, str) or v is None else float(v), r)) for r in rows]), open(W / 'shift_vs_height.json', 'w'), indent=1, ensure_ascii=False); print(json.dumps(out), flush=True)
fig, axs = plt.subplots(1, 2, figsize=(16, 6.5)); hh = np.linspace(0, h.max(), 50)
for ax, v, p, t in ((axs[0], ny, pn, '남북 이동 (북 +)'), (axs[1], ex, pe, '동서 이동 (동 +)')):
    ax.scatter(h, v, s=40, c=np.where(lowm, 'tab:blue', 'tab:red')); ax.plot(hh, np.polyval(p, hh), 'k--', label=f'직선: {p[1]:+.2f} m + {p[0]:+.3f} × 높이')
    ax.axhline(0, c='0.6'); ax.set_xlabel('건물 높이 (m, 건축물정보)'); ax.set_ylabel(f'{t}, 사진에 맞추는 이동 (m)'); ax.legend(); ax.grid(alpha=0.3)
    ax.set_title(f'{t}\n파랑 25 m 이하 / 빨강 25 m 초과 (건물마다 따로 맞춤, n={len(rows)})')
plt.suptitle('높이와 무관하게 일정하면 = V-World 외곽선 위치 오차, 높이에 비례하면 = 항공사진 기울어짐', fontsize=14)
plt.tight_layout(); o = '/home/diglab/workspace/workspace/instant_nurec/res_wjdaksry/1106/vworld_shift_vs_height.png'; plt.savefig(o, dpi=95); print(o)
