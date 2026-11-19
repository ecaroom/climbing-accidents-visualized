"""CVD check for the discipline palette (Python port of the dataviz skill's
OKLab dE x100 check; node isn't installed). Usage: check_palette.py name=#hex ..."""
import sys, itertools, numpy as np
M = {'normal': np.eye(3),
     'protan': np.array([[0.152286,1.052583,-0.204868],[0.114503,0.786281,0.099216],[-0.003882,-0.048116,1.051998]]),
     'deutan': np.array([[0.367322,0.860646,-0.227968],[0.280085,0.672501,0.047413],[-0.011820,0.042940,0.968881]]),
     'tritan': np.array([[1.255528,-0.076749,-0.178779],[-0.078411,0.930809,0.147602],[0.004733,0.691367,0.303900]])}
def lin(h): c = np.array([int(h[i:i+2],16)/255 for i in (1,3,5)]); return np.where(c<=0.04045, c/12.92, ((c+0.055)/1.055)**2.4)
def oklab(rgb):
    rgb = np.clip(rgb,0,1)
    l,m,s = np.cbrt(np.array([[0.4122214708,0.5363325363,0.0514459929],[0.2119034982,0.6806995451,0.1073969566],[0.0883024619,0.2817188376,0.6299787005]]) @ rgb)
    return np.array([0.2104542553*l+0.7936177850*m-0.0040720468*s, 1.9779984951*l-2.4285922050*m+0.4505937099*s, 0.0259040371*l+0.7827717662*m-0.8086757660*s])
def lum(h): r,g,b = lin(h); return 0.2126*r+0.7152*g+0.0722*b
pal = dict(a.split('=') for a in sys.argv[1:])
worst = {}
for (n1,h1),(n2,h2) in itertools.combinations(pal.items(),2):
    d = {k: 100*np.linalg.norm(oklab(m@lin(h1))-oklab(m@lin(h2))) for k,m in M.items()}
    k = min(d, key=d.get); print(f"{n1:>10} vs {n2:<10} " + "  ".join(f"{t}={v:5.1f}" for t,v in d.items()) + ("   <-- below 8" if d[k]<8 else ""))
for n,h in pal.items():
    for surf,sh in [('light','#ffffff'),('dark','#1a1a19')]:
        a,b = sorted([lum(h),lum(sh)]); cr=(b+0.05)/(a+0.05)
    print(f"{n:>10} {h}  contrast vs white {(1.05)/(lum(h)+0.05):.2f}  vs dark {(lum(h)+0.05)/(lum('#1a1a19')+0.05):.2f}")
