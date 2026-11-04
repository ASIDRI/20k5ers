"""DEW as a daily trigger in the weekly trend: close crosses the WMA30 in the trend direction with DPO20 on the same
side. Entry at that close; stop beyond the extreme of the last 10 days + 0.1 ATR; exit at the stop, at a fixed 2R
target, or (trend exit) at the first close back across the WMA. Point-in-time: weekly state of the last closed week."""
import sys, os
from concurrent.futures import ProcessPoolExecutor
sys.path[:0]=["research/strategy","backtest/src"]
import numpy as np, pandas as pd
syms=[f[6:-4] for f in sorted(os.listdir("research/strategy/out")) if f.startswith("v2n37_")]
def one(sym):
    import trader_strategy as T
    from setup_study import load
    from candle_avail import complete_times
    T.apply_profile(sym)
    d,w=load(sym,"D1"),load(sym,"W1")
    out=[]
    for dirn in (-1,1):
        sg=1 if dirn==-1 else -1
        def px(df):
            o,h,l,c=(df[k].values.astype(float) for k in ("open","high","low","close"))
            return (o,h,l,c) if sg==1 else (-o,-l,-h,-c)
        st=T.weekly_structure(*px(w))[0]
        wdone=complete_times(w["time"],"W1").values; ddone=complete_times(d["time"],"D1").values
        o,h,l,c=px(d); a=T.atr(h,l,c)
        wts=np.arange(1,31,dtype=float); wma=np.r_[np.full(29,np.nan),np.convolve(c,wts[::-1]/wts.sum(),"valid")]
        sma=pd.Series(c).rolling(20).mean().values; dpo=c-np.r_[np.full(11,np.nan),sma[:-11]]
        sig=(c<wma)&(dpo<0)
        days=[T.day_label(x) for x in d.time]
        k=40; busy=-1
        while k<len(c)-1:
            if days[k]<"2016-01-01" or days[k]>="2026-01-01" or k<=busy or not (sig[k] and not sig[k-1]):
                k+=1; continue
            wi=int(np.searchsorted(wdone,ddone[k],"right"))-1
            if wi<0 or st[wi]!=-1: k+=1; continue
            e=c[k]; sl=np.max(h[k-9:k+1])+0.1*a[k]; risk=sl-e
            if risk<=0: k+=1; continue
            cost=T.cost_price(sym,abs(e))
            res={}
            for mode in ("2R","trend"):
                for i in range(k+1,len(c)):
                    if h[i]>=sl: r=-1.0; break
                    if mode=="2R" and l[i]<=e-2*risk: r=2.0; break
                    if mode=="trend" and c[i]>wma[i]: r=(e-c[i])/risk; break
                else: r=(e-c[-1])/risk
                res[mode]=(r-cost/risk, i)
            out.append((sym,days[k],dirn,res["2R"][0],res["trend"][0]))
            busy=max(res["2R"][1],res["trend"][1]); k+=1
    return out
if __name__=="__main__":
    with ProcessPoolExecutor(4) as ex: res=[x for y in ex.map(one,syms) for x in y]
    df=pd.DataFrame(res,columns=["sym","day","dir","R2","Rtrend"])
    for col in ("R2","Rtrend"):
        r=df[col]; h1=df[df.day<"2021"][col].sum(); h2=df[df.day>="2021"][col].sum()
        print(f"DEW-trigger exit {col}: {len(r)} trades, win {np.mean(r>0):.0%}, R {r.sum():+.1f} (16-20 {h1:+.1f}, 21-25 {h2:+.1f}), gem {r.mean():+.3f}, t {r.mean()/r.std()*np.sqrt(len(r)):.2f}")
    for s in ("EURUSD","GBPJPY"):
        x=df[df.sym==s]; print(f"  {s}: {len(x)} trades, R2 {x.R2.sum():+.1f}, Rtrend {x.Rtrend.sum():+.1f}")
    if len(sys.argv) > 1: df.to_csv(sys.argv[1], index=False)
