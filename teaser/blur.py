import glob, os, numpy as np
from PIL import Image
from collections import defaultdict
g = defaultdict(list)
for f in sorted(glob.glob('sub3/*.png')): g[os.path.basename(f).split('_')[0]].append(f)
for fid, fs in g.items():
    acc = sum(np.asarray(Image.open(f).convert('RGB')).astype(np.float32) for f in fs) / len(fs)
    Image.fromarray(np.clip(acc + .5, 0, 255).astype(np.uint8)).save(f'f3/{fid}.jpg', quality=95)
print('blurred', len(g))
