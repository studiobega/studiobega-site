"""Courbes de niveau d'un relief ardennais imaginaire : plateaux, une vallée encaissée en méandres."""
import numpy as np, contourpy
W, H, N = 1600, 640, 2
rng = np.random.default_rng(7)
x = np.linspace(0, W, 400); y = np.linspace(0, H, 160)
X, Y = np.meshgrid(x, y)
Z = np.zeros_like(X)
for _ in range(26):   # collines douces
    cx, cy = rng.uniform(-100, W + 100), rng.uniform(-100, H + 100)
    s = rng.uniform(120, 340); a = rng.uniform(.4, 1.0)
    Z += a * np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (2 * s * s))
# vallée en méandres (une rivière qui serpente de gauche à droite)
mid = H * .58 + 110 * np.sin(X / 230) + 40 * np.sin(X / 90 + 1)
Z -= 1.4 * np.exp(-((Y - mid) ** 2) / (2 * 70 ** 2))
Z += .15 * np.sin(X / 37 + Y / 53)
gen = contourpy.contour_generator(x, y, Z)
paths = []
for lv in np.linspace(Z.min() + .05, Z.max() - .05, 34):
    for seg in gen.lines(lv):
        if len(seg) < 6: continue
        seg = seg[::2] if len(seg) > 12 else seg
        paths.append('M' + 'L'.join(f'{a:.0f},{b:.0f}' for a, b in seg))
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice">'
       f'<path d="{" ".join(paths)}" fill="none" stroke="#d6d4cc" stroke-width="1" vector-effect="non-scaling-stroke"/></svg>')
open('assets/topo.svg', 'w').write(svg); print(len(svg)//1024, 'Ko')
