import math
L=100.0; d=0.740
path="ring3d_land.txt"
lines=open(path,encoding="utf-8",errors="ignore").read().splitlines()
hdr=0
for i,ln in enumerate(lines):
    if ln.strip().startswith("%"): hdr=i
    else: break
rows=[ln for ln in lines[hdr+1:] if ln.strip() and not ln.strip().startswith("%")]
def parse(ln):
    v=ln.split()[1:]; n=len(v)//4; out=[]
    for k in range(n):
        try: out.append((float(v[4*k]),float(v[4*k+1]),float(v[4*k+2]),float(v[4*k+3])))
        except ValueError: out.append((float('nan'),)*4)
    return out

bylam={}
for ln in rows:
    rec=parse(ln)
    if not rec: continue
    # wavelength of this ray = first non-nan lambda entry in the row
    lam0=float('nan')
    for (_,_,_,lam) in rec:
        if lam==lam: lam0=lam; break
    # landing radius: first sample with z in [95,105]
    for (qx,qy,qz,lam) in rec:
        if qz==qz and 95.0<=qz<=105.0:
            r=math.hypot(qx,qy)
            if r>1.0 and lam0==lam0:
                bylam.setdefault(round(lam0,1),[]).append(r)
            break

print(f"{'lambda(nm)':>11} {'count':>6} {'rho_sim':>9} {'rho_theory':>11} {'err':>7}")
tot=0
for lam in sorted(bylam):
    rs=bylam[lam]; rho=sum(rs)/len(rs); tot+=len(rs)
    s=(lam/1000.0)/d; th=L*math.tan(math.asin(s)) if s<1 else float('nan')
    err=(rho-th)/th*100 if th==th else float('nan')
    print(f"{lam:11.1f} {len(rs):6d} {rho:9.2f} {th:11.2f} {err:6.2f}%")
print("total diffracted rays landed:", tot)
