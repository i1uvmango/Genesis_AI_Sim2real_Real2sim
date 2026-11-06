"""V-World probe for a 200 m x 200 m Teheran-ro test box (around Yeoksam station).
Needs env VWORLD_KEY. The key is never printed or saved: every saved body/URL has it replaced by <KEY>.
Calls (endpoints from the official developer pages saved in docs/):
  Q3  WMTS GetCapabilities + Satellite tiles at zoom 19 (max per docs) and 18   -> raw/, samples/
  Q1  WFS building footprints (GIS building layer) in the box                   -> raw/
  Q4  2D data API: none of the 158 listed services is an HD-map layer, so nothing is called here
Usage: python -I probe.py
"""
import os, sys, json, math, pathlib, urllib.request, urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
KEY = os.environ.get('VWORLD_KEY', '')
if not KEY and (HERE / '.env').exists():   # .env is gitignored (genesis-doc/.gitignore: *.env)
    for line in (HERE / '.env').read_text().splitlines():
        if line.startswith('VWORLD_KEY='):
            KEY = line.split('=', 1)[1].strip()
if not KEY:
    sys.exit('VWORLD_KEY is not set (env or .env)')
DOMAIN = 'https://github.com/i1uvmango/Genesis_AI_Sim2real_Real2sim'
RAW = HERE / 'raw'; SMP = HERE / 'samples'; RAW.mkdir(exist_ok=True); SMP.mkdir(exist_ok=True)
LAT, LON = 37.5007, 127.0365          # Yeoksam station, Teheran-ro
DLAT, DLON = 0.0009, 0.00113          # about +-100 m
LOG = []


def red(s):
    return s.replace(KEY, '<KEY>') if isinstance(s, str) else s


def get(url, name, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': 'vworld-probe/0.1', 'Referer': DOMAIN})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            code, ctype, body = r.status, r.headers.get('Content-Type', ''), r.read()
    except urllib.error.HTTPError as e:
        code, ctype, body = e.code, e.headers.get('Content-Type', ''), e.read()
    except Exception as e:
        code, ctype, body = -1, '', repr(e).encode()
    is_img = ctype.startswith('image/')
    out = (SMP if is_img else RAW) / name
    if is_img:
        out.write_bytes(body)
    else:
        out = out.with_suffix(out.suffix + '.txt')
        out.write_text(red(body.decode('utf-8', 'replace')))
    LOG.append({'name': name, 'url': red(url), 'http': code, 'content_type': ctype, 'bytes': len(body), 'saved': str(out.relative_to(HERE))})
    print(name, code, ctype, len(body), flush=True)
    return code, ctype, body


def tile(lat, lon, z):
    n = 2 ** z; x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return x, y


# Q3: orthophoto tiles
get(f'https://api.vworld.kr/req/wmts/1.0.0/{KEY}/WMTSCapabilities.xml', 'wmts_capabilities.xml')
for z in (19, 18):
    x, y = tile(LAT, LON, z)
    get(f'https://api.vworld.kr/req/wmts/1.0.0/{KEY}/Satellite/{z}/{y}/{x}.jpeg', f'satellite_z{z}_{y}_{x}.jpeg')
    mpp = 156543.03392 * math.cos(math.radians(LAT)) / 2 ** z
    LOG[-1]['m_per_px_nominal'] = round(mpp, 4)

# Q1: building footprints by WFS (layer name from the WFS service list; result is 2D polygons + attributes)
bbox = f'{LAT - DLAT},{LON - DLON},{LAT + DLAT},{LON + DLON}'
q = dict(key=KEY, domain=DOMAIN, SERVICE='WFS', VERSION='1.1.0', REQUEST='GetFeature', TYPENAME='lt_c_spbd',
         BBOX=bbox + ',EPSG:4326', SRSNAME='EPSG:4326', OUTPUT='application/json', MAXFEATURES='50')
get('https://api.vworld.kr/req/wfs?' + urllib.parse.urlencode(q), 'wfs_lt_c_spbd.json')

(HERE / 'probe_log.json').write_text(json.dumps(LOG, indent=1, ensure_ascii=False))
print('log ->', HERE / 'probe_log.json')
