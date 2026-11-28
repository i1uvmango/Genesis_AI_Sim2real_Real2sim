import json, numpy as np, sys
a = np.load('/home/diglab/workspace/workspace/instant_nurec/work/pai058_20261107/cameras.npz'); CAM = {k: p for k, p in zip(a['keys'], a['poses'])}
out = []
for L in (60, 120):
    c = CAM[f'front|{L}']; fw = c[:3, 2].copy(); fw[2] = 0; fw /= np.linalg.norm(fw); left = np.array([-fw[1], fw[0], 0])
    for oi in range(16):
        for yi in range(7):
            th = np.deg2rad(yi * 5); Rz = np.array([[np.cos(th), -np.sin(th), 0], [np.sin(th), np.cos(th), 0], [0, 0, 1]])
            m = c.copy(); m[:3, :3] = Rz @ c[:3, :3]; m[:3, 3] = c[:3, 3] + left * oi * 0.2
            out.append({'name': f'v{L:03d}_o{oi:02d}_y{yi}', 'c2w': m.tolist(), 'image': '', 'mask': ''})
json.dump(out, open('viewer_poses.json', 'w')); print(len(out))
