"""Bit-accurate golden model of the RTL QRS detector (integer arithmetic only)."""
import numpy as np
FS=360
class P:  # parameters shared with RTL
    BL_SHIFT=7          # baseline IIR: fc ~ fs/(2*pi*128) = 0.45 Hz
    FIR_Q=12            # FIR coefficient fraction bits
    MWI=54              # 150 ms
    INIT=720            # 2 s learning phase
    REFR=72             # 200 ms
    TWAVE_GAP=130       # 360 ms
    SB=64; SF=4         # R-peak search window: [p-SB, p-SF]
def sat(v,W): return np.clip(v,-(1<<(W-1)),(1<<(W-1))-1)
def baseline_remove(x,W=16):
    bl=0; hp=np.zeros(len(x),dtype=np.int64)
    for n,v in enumerate(x):
        bl_new=bl+((((int(v))<<8)-bl)>>P.BL_SHIFT)
        hp[n]=int(v)-(bl_new>>8); bl=bl_new
    return sat(hp,W)
def fir(hp,h,W=16):
    acc=np.convolve(hp,np.array(h,dtype=np.int64))[:len(hp)]
    return sat(acc>>P.FIR_Q,W)
def deriv(bp,W=16):
    z=np.concatenate([np.zeros(4,dtype=np.int64),bp])
    d=(2*z[4:]+z[3:-1]-z[1:-3]-2*z[:-4])>>3
    return sat(d,W)
def mwi(d,sqshift=0,SW=32):
    sq=np.minimum((d*d)>>sqshift,(1<<SW)-1); c=np.cumsum(sq); s=c.copy(); s[P.MWI:]=c[P.MWI:]-c[:-P.MWI]
    return sq,s
def decide(env):
    """peak detect + adaptive threshold + refractory + T-wave check + search-back"""
    beats=[]; N=len(env)
    mx=0; sm=0; SPKI=0; NPKI=0
    have=False; last_p=0; last_pk=0; rr_avg=0
    cand_v=0; cand_i=0; cand_ok=False
    thr_log=np.zeros(N,dtype=np.int64)
    def upd_rr(p):
        nonlocal rr_avg
        rr=p-last_p
        rr_avg = rr if rr_avg==0 else rr_avg+((rr-rr_avg)>>3)
    for n in range(N):
        e=int(env[n])
        if n<P.INIT:
            mx=max(mx,e); sm+=e
            if n==P.INIT-1: SPKI=mx>>2; NPKI=sm>>11
            continue
        e1=int(env[n-1]); e2=int(env[n-2])
        THR=NPKI+((SPKI-NPKI)>>2) if SPKI>NPKI else NPKI
        thr_log[n]=THR
        if e1>e2 and e1>=e:
            p=n-1; gap=p-last_p
            okgap=(not have) or gap>=P.REFR
            if e1>THR and okgap:
                if have and gap<P.TWAVE_GAP and e1<(last_pk>>1):
                    NPKI=NPKI-(NPKI>>3)+(e1>>3)
                else:
                    SPKI=SPKI-(SPKI>>3)+(e1>>3)
                    if have: upd_rr(p)
                    beats.append((p,n)); last_p=p; last_pk=e1; have=True; cand_ok=False
            elif e1<=THR:
                NPKI=NPKI-(NPKI>>3)+(e1>>3)
                if e1>(THR>>1) and okgap and (not cand_ok or e1>cand_v):
                    cand_v=e1; cand_i=p; cand_ok=True
        if have and rr_avg!=0 and cand_ok and (n-last_p)>(rr_avg+(rr_avg>>1)+(rr_avg>>2)):
            SPKI=SPKI-(SPKI>>2)+(cand_v>>2)
            upd_rr(cand_i)
            beats.append((cand_i,n)); last_p=cand_i; last_pk=cand_v; have=True; cand_ok=False
    return beats,thr_log
def locate(hp,beats):
    out=[]
    for p,n in beats:
        lo=p-P.SB; hi=p-P.SF
        seg=np.abs(hp[lo:hi+1]); out.append(lo+int(np.argmax(seg)))
    return out
def run(x,h,W=16,sqshift=0,SW=32):
    x=sat(x,W); hp=baseline_remove(x,W); bp=fir(hp,h,W); d=deriv(bp,W); sq,env=mwi(d,sqshift,SW)
    beats,thr=decide(env); r=locate(hp,beats)
    return dict(hp=hp,bp=bp,d=d,env=env,beats=beats,rpeaks=r,thr=thr)
def score(det,ref,tol=54,start=1080):
    det=sorted(d for d in det if d>=start); ref=sorted(r for r in ref if r>=start)
    used=set(); tp=0; err=[]
    for r in ref:
        best=None
        for k,dv in enumerate(det):
            if k in used: continue
            if abs(dv-r)<=tol and (best is None or abs(dv-r)<abs(det[best]-r)): best=k
        if best is not None: used.add(best); tp+=1; err.append(det[best]-r)
    fp=len(det)-tp; fn=len(ref)-tp
    se=tp/(tp+fn) if tp+fn else 0; ppv=tp/(tp+fp) if tp+fp else 0
    f1=2*se*ppv/(se+ppv) if se+ppv else 0
    return dict(TP=tp,FP=fp,FN=fn,Se=se*100,PPV=ppv*100,F1=f1*100,mean_err=float(np.mean(err)) if err else 0,abs_err_ms=float(np.mean(np.abs(err))/FS*1000) if err else 0)
