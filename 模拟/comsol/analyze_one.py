import math
path="ring3d_land.txt"
lines=open(path,encoding="utf-8",errors="ignore").read().splitlines()
hdr=0
for i,ln in enumerate(lines):
    if ln.strip().startswith("%"): hdr=i
    else: break
rows=[ln for ln in lines[hdr+1:] if ln.strip() and not ln.strip().startswith("%")]
def parse(ln):
    v=ln.split()[1:]
    n=len(v)//4
    out=[]
    for k in range(n):
        try: out.append((float(v[4*k]),float(v[4*k+1]),float(v[4*k+2]),float(v[4*k+3])))
        except ValueError: out.append((float('nan'),)*4)
    return out
# find ray with max final radius
best=None;bestr=-1
for ln in rows:
    rec=parse(ln)
    if not rec: continue
    fx,fy,fz,lam=rec[-1]
    r=math.hypot(fx,fy)
    if r>bestr: bestr=r;best=rec
print("max final radius ray, lambda=",best[0][3])
print("  idx  z        r")
for k,(qx,qy,qz,lam) in enumerate(best):
    print(f"  {k:3d}  {qz:8.3f}  {math.hypot(qx,qy):8.4f}")
