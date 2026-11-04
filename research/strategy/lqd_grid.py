"""Setup-4 grid through the engine (guarded): LQD_ENTRY x LQD_FILTER on all 37 instruments, split EURUSD / other 36 and
with / against the weekly trend.  python research/strategy/lqd_grid.py '[{"LQD_ENTRY": "close", "LQD_FILTER": null}]' out.csv"""
import sys, os, json, itertools
from concurrent.futures import ProcessPoolExecutor
sys.path[:0]=["research/strategy","backtest/src"]
import numpy as np, pandas as pd
syms=[f[6:-4] for f in sorted(os.listdir("research/strategy/out")) if f.startswith("v2n37_")]
def one(args):
    sym,cfg=args
    import trader_strategy as T
    from setup_study import load
    T.PROFILES["EURUSD"].update(LQD=True, LQD_CTX="both"); T.DEFAULT_PROFILE.update(LQD=True, LQD_CTX="both")
    for k,v in cfg.items(): setattr(T,k,v)
    d,w=load(sym,"D1"),load(sym,"W1")
    try: m=load(sym,"MN")
    except Exception: m=None
    tr=[]
    for dirn in (-1,1): tr+=T.run_view(sym,d,w,dirn,"2016-01-01","2026-01-01",[],m)
    return [(sym,t["entry_day"],t["dir"],"trend" if "met trend" in t["pattern"] else "tegen",t["R"],bool(t["t1_day"])) for t in tr if t["setup"]=="lqd"]
rows=[]
grid=json.loads(sys.argv[1])
for cfg in grid:
    with ProcessPoolExecutor(4) as ex: df=pd.DataFrame([x for y in ex.map(one,[(s,cfg) for s in syms]) for x in y],columns=["sym","day","dir","ctx","R","t1"])
    for grp,g in (("EURUSD",df[df.sym=="EURUSD"]),("andere36",df[df.sym!="EURUSD"])):
        for ctx in ("trend","tegen"):
            x=g[g.ctx==ctx]; r=x.R
            if len(r)<2: continue
            rows.append(dict(cfg=json.dumps(cfg),grp=grp,ctx=ctx,n=len(r),win=round(x.t1.mean(),2),R=round(r.sum(),1),gem=round(r.mean(),3),
                             h1=round(x[x.day<"2021"].R.sum(),1),h2=round(x[x.day>="2021"].R.sum(),1),t=round(r.mean()/r.std()*np.sqrt(len(r)),2)))
    print(json.dumps(cfg), " | ".join(f"{r_['grp']}-{r_['ctx']}: n{r_['n']} w{r_['win']:.0%} R{r_['R']:+.1f} t{r_['t']:+.2f}" for r_ in rows[-4:]), flush=True)
pd.DataFrame(rows).to_csv(sys.argv[2],index=False)
