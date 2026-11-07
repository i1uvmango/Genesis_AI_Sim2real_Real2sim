"""Example figure around the ADI block (Samseong-ro): NGII HD map layers | V-World buildings (LT_C_BLDGINFO, height m) |
both over V-World orthophoto (WMTS Satellite z19). Requests: 1 WFS + 16 tiles. Key from .env, never printed.
Output: res_wjdaksry/1106/hd_vworld_example.png"""
import sys, io, json, math, glob, pathlib, urllib.request, urllib.parse, numpy as np
from PIL import Image
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; plt.rcParams['font.family'] = 'Noto Sans CJK JP'; plt.rcParams['axes.unicode_minus'] = False
from matplotlib.collections import PolyCollection, LineCollection
sys.path.insert(0, '/home/diglab/workspace/workspace/ngii_hdmap'); from shp import read_shp, read_dbf
HERE = pathlib.Path(__file__).resolve().parent
K = [l.split('=', 1)[1].strip() for l in (HERE / '.env').read_text().splitlines() if l.startswith('VWORLD_KEY=')][0]
D = 'https://github.com/i1uvmango/Genesis_AI_Sim2real_Real2sim'; UA = {'User-Agent': 'vworld-probe/0.1', 'Referer': D}
LAT0, LON0, HALF = 37.50620, 127.05700, 130.0; Rr = 6378137.0
def enu(lat, lon): return np.c_[np.radians(lon - LON0) * Rr * math.cos(math.radians(LAT0)), np.radians(lat - LAT0) * Rr]
def utm_inv(E, N, zone=52):
    a = 6378137.0; f = 1 / 298.257223563; k0 = 0.9996; e2 = f * (2 - f); ep2 = e2 / (1 - e2); e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    x = E - 500000.0; M = N / k0; mu = M / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    p1 = mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * np.sin(2 * mu) + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * np.sin(4 * mu) + (151 * e1 ** 3 / 96) * np.sin(6 * mu)
    N1 = a / np.sqrt(1 - e2 * np.sin(p1) ** 2); T1 = np.tan(p1) ** 2; C1 = ep2 * np.cos(p1) ** 2; R1 = a * (1 - e2) / (1 - e2 * np.sin(p1) ** 2) ** 1.5; Dd = x / (N1 * k0)
    lat = p1 - (N1 * np.tan(p1) / R1) * (Dd ** 2 / 2 - (5 + 3 * T1 + 10 * C1 - 4 * C1 ** 2 - 9 * ep2) * Dd ** 4 / 24 + (61 + 90 * T1 + 298 * C1 + 45 * T1 ** 2 - 252 * ep2 - 3 * C1 ** 2) * Dd ** 6 / 720)
    lon = math.radians((zone - 1) * 6 - 180 + 3) + (Dd - (1 + 2 * T1 + C1) * Dd ** 3 / 6 + (5 - 2 * C1 + 28 * T1 - 3 * C1 ** 2 + 8 * ep2 + 24 * T1 ** 2) * Dd ** 5 / 120) / np.cos(p1)
    return np.degrees(lat), np.degrees(lon)
# ---- HD map layers
SEC = '/home/diglab/workspace/workspace/ngii_hdmap/gangnamgu/SEC008_삼성로/HDMap_UTM52N_타원체고'
def layer(name):
    try: G = read_shp(f'{SEC}/{name}.shp')
    except Exception: return []
    out = []
    for g in G:
        if g is None: continue
        g = np.atleast_2d(g); la, lo = utm_inv(g[:, 0], g[:, 1]); P = enu(la, lo)
        if (np.abs(P) < HALF * 1.3).all(1).any(): out.append(P)
    return out
HD = {n: layer(n) for n in ['A3_DRIVEWAYSECTION', 'A4_SUBSIDIARYSECTION', 'B2_SURFACELINEMARK', 'B3_SURFACEMARK', 'A2_LINK', 'C1_TRAFFICLIGHT', 'B1_SAFETYSIGN']}
print({k: len(v) for k, v in HD.items()}, flush=True)
# ---- V-World buildings (1 WFS request)
dlat = math.degrees(HALF / Rr); dlon = math.degrees(HALF / (Rr * math.cos(math.radians(LAT0))))
q = dict(key=K, domain=D, SERVICE='WFS', VERSION='1.1.0', REQUEST='GetFeature', TYPENAME='lt_c_bldginfo', BBOX=f'{LAT0-dlat},{LON0-dlon},{LAT0+dlat},{LON0+dlon},EPSG:4326',
         SRSNAME='EPSG:4326', OUTPUT='application/json', MAXFEATURES='1000')
d = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.vworld.kr/req/wfs?' + urllib.parse.urlencode(q), headers=UA), timeout=60).read().decode('utf-8'))
json.dump(d, open(HERE / 'example' / 'adi_bldginfo.geojson', 'w'), ensure_ascii=False)
B = []
for f in d['features']:
    g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]; pr = f['properties']
    h = pr.get('height') or 0; fl = pr.get('grnd_flr') or 0; hh = h if h and h > 0 else (fl * 3.3 + 1.5 if fl else 15.0)
    for p in polys: ext = np.array(p[0]); B.append((enu(ext[:, 1], ext[:, 0]), hh, pr.get('bld_nm'), h > 0))
print('buildings', len(B), 'with height(m)', sum(b[3] for b in B), flush=True)
# ---- orthophoto z19 tiles
z = 19; n = 2 ** z
def tile_xy(lat, lon): return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
x0, y0 = tile_xy(LAT0 + dlat, LON0 - dlon); x1, y1 = tile_xy(LAT0 - dlat, LON0 + dlon)
tx = range(int(x0), int(x1) + 1); ty = range(int(y0), int(y1) + 1); mos = Image.new('RGB', (256 * len(tx), 256 * len(ty)))
for j, yy in enumerate(ty):
    for i, xx in enumerate(tx):
        b = urllib.request.urlopen(urllib.request.Request(f'https://api.vworld.kr/req/wmts/1.0.0/{K}/Satellite/{z}/{yy}/{xx}.jpeg', headers=UA), timeout=40).read()
        mos.paste(Image.open(io.BytesIO(b)).convert('RGB'), (i * 256, j * 256))
print('tiles', len(tx) * len(ty), flush=True); mos.save(HERE / 'example' / 'ortho_z19.png')
def tile2ll(xx, yy): return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * yy / n)))), xx / n * 360 - 180
la_t, lo_l = tile2ll(tx[0], ty[0]); la_b, lo_r = tile2ll(tx[-1] + 1, ty[-1] + 1); (xl, yt), (xr, yb) = enu(np.array([la_t, la_b]), np.array([lo_l, lo_r]))
ext = [xl, xr, yb, yt]; json.dump(dict(ext=[float(v) for v in ext], lat0=LAT0, lon0=LON0), open(HERE / 'example' / 'ortho_z19.json', 'w'))
# ---- figure
fig, axs = plt.subplots(1, 3, figsize=(27, 9.5))
def draw_hd(ax, light=False):
    for P in HD['A3_DRIVEWAYSECTION']: ax.fill(P[:, 0], P[:, 1], color='0.85' if not light else 'none', ec='0.4', lw=0.6, alpha=0.9 if not light else 1)
    for P in HD['A4_SUBSIDIARYSECTION']: ax.fill(P[:, 0], P[:, 1], color='#f2d7a6' if not light else 'none', ec='#c08a2e', lw=0.6, alpha=0.8 if not light else 1)
    ax.add_collection(LineCollection([P for P in HD['B2_SURFACELINEMARK']], colors='#ffd400' if light else 'k', lw=1.0))
    for P in HD['B3_SURFACEMARK']: ax.fill(P[:, 0], P[:, 1], color='#e8381c', alpha=0.9)
    ax.add_collection(LineCollection([P for P in HD['A2_LINK']], colors='#2b7bff', lw=0.7, linestyles='--'))
    for nm, mk, c in (('C1_TRAFFICLIGHT', '^', '#00a651'), ('B1_SAFETYSIGN', 's', '#7a2bd6')):
        if HD[nm]: P = np.concatenate(HD[nm]); ax.scatter(P[:, 0], P[:, 1], marker=mk, c=c, s=30, zorder=5)
draw_hd(axs[0]); axs[0].set_title('정밀도로지도 (국토지리정보원, SEC008 삼성로)\n회색 차도면 / 주황 보도 / 검정 차선 / 빨강 노면표시 / 파랑 점선 차로 중심선 / 초록 신호등 / 보라 표지판', fontsize=12)
pc = PolyCollection([b[0] for b in B], array=np.array([b[1] for b in B]), cmap='viridis', ec='k', lw=0.4); axs[1].add_collection(pc)
plt.colorbar(pc, ax=axs[1], shrink=0.75, label='건물 높이 (m)')
for P, hh, nm, real in B:
    c = P.mean(0)
    if hh > 40 and np.abs(c).max() < HALF: axs[1].text(c[0], c[1], f'{nm or ""}\n{hh:.0f} m', fontsize=8, ha='center', va='center', color='w')
axs[1].set_title('V-World 건축물정보 (LT_C_BLDGINFO)\n건물 위치·외곽선 + 실제 높이(m), 2D → 높이로 세우면 박스(LoD1)', fontsize=12)
axs[2].imshow(np.asarray(mos), extent=ext); draw_hd(axs[2], light=True)
for P, hh, nm, real in B: axs[2].plot(np.r_[P[:, 0], P[0, 0]], np.r_[P[:, 1], P[0, 1]], c='cyan', lw=1.0)
axs[2].set_title('V-World 정사영상 (줌 19, 픽셀당 0.24 m) 위에 겹침\n노랑 차선·주황 보도 = 정밀도로지도, 하늘색 = V-World 건물', fontsize=12)
for ax in axs: ax.set_aspect('equal'); ax.set_xlim(-HALF, HALF); ax.set_ylim(-HALF, HALF); ax.set_xlabel('동쪽 (m)'); ax.set_ylabel('북쪽 (m)')

plt.tight_layout(); out = '/home/diglab/workspace/workspace/instant_nurec/res_wjdaksry/1106/hd_vworld_example.png'; plt.savefig(out, dpi=100); print(out)
