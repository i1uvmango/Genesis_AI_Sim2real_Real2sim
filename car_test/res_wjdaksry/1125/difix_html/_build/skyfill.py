"""Fill the black (sky-masked) area of ADI k5 renders with sky colour measured from the real photos.
Sky colour = per-row median of the SAM3 sky pixels of the rear-camera photos of the block (the 'fwd' render direction is the rear camera),
smoothed over rows; the black area touching the top border is replaced by that gradient with a 2 px feather. CPU only."""
import sys, glob, os, numpy as np, cv2
from PIL import Image
A = '/home/diglab/workspace/workspace/instant_nurec/work/seq60_20261105/images'
SKY = np.load('/home/diglab/workspace/workspace/instant_nurec/results/adi/seq60/scene_L000-300_lidar/k1/joint/k8_b000_299/sky.npz')
def gradient(labels, H=540, W=1440):
    rows = [[] for _ in range(H)]
    for l in labels:
        k = f'rear_{l:04d}'
        if k not in SKY.files: continue
        m = np.unpackbits(SKY[k], axis=1)[:, :W].astype(bool); p = np.asarray(Image.open(f'{A}/{k}.jpg').convert('RGB'))
        for y in np.where(m.any(1))[0]: rows[y].append(p[y][m[y]])
    g = np.full((H, 3), np.nan)
    for y in range(H):
        if rows[y]: g[y] = np.median(np.concatenate(rows[y]), 0)
    v = ~np.isnan(g[:, 0]); idx = np.arange(H)
    for c in range(3): g[:, c] = np.interp(idx, idx[v], g[v, c])
    g = cv2.GaussianBlur(g[None].astype(np.float32), (1, 0), sigmaX=1, sigmaY=0)[0] if False else g
    k = np.exp(-0.5 * (np.arange(-40, 41) / 15.0) ** 2); k /= k.sum()
    return np.stack([np.convolve(np.pad(g[:, c], 40, mode='edge'), k, 'valid') for c in range(3)], 1), v.sum()
def fill(render, G):
    r = np.asarray(Image.open(render).convert('RGB')).astype(np.float32); H, W = r.shape[:2]
    dark = (r.max(2) < 14).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(dark, connectivity=4)
    top = [i for i in range(1, n) if st[i, cv2.CC_STAT_TOP] < 30 and st[i, cv2.CC_STAT_AREA] > 150]   # black blobs reaching the top band = masked sky
    hole = cv2.dilate(np.isin(lab, top).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32)
    gy = cv2.resize(G[None].astype(np.float32), (H, 1))[0] if G.shape[0] != H else G
    sky = np.repeat(gy[:, None, :], W, 1)
    a = cv2.GaussianBlur(hole, (0, 0), 2.0)[..., None]
    return (sky * a + r * (1 - a)).clip(0, 255).astype(np.uint8), hole.mean()
if __name__ == '__main__':
    src, dst, lab0, lab1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]); w = int(sys.argv[5]) if len(sys.argv) > 5 else 1200
    G, nrow = gradient(range(lab0, lab1)); print('sky rows measured', nrow, 'top', G[0].round(), 'row 150', G[150].round())
    os.makedirs(dst, exist_ok=True)
    for f in sorted(glob.glob(f'{src}/*/st_*_fwd_*.jpg') + glob.glob(f'{src}/*/st_chase_*.jpg')):
        s = f.split('/')[-2]; v = os.path.basename(f)[3:].rsplit('_', 1)[0]
        o, fr = fill(f, G); im = Image.fromarray(o); im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS); im.save(f'{dst}/{v}_{s}.jpg', quality=86)
    print('done')
