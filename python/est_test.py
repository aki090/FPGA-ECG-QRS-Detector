import numpy as np, sys
sys.path.insert(0,'python')
import golden as g
P=g.P
x0=np.load('sim/ecg.npy'); nz=np.load('sim/noise.npy'); h=list(np.load('python/fir_q12.npy'))
ref=[int(v) for v in open('data/ref_beats.txt').read().split()]
def decide2(env,mode,p):
    beats=[]; N=len(env); mx=0; sm=0; SPKI=0; NPKI=0; have=False; last_p=0; last_pk=0; rr_avg=0
    cand_v=0; cand_i=0; cand_ok=False
    def upd(pp):
        nonlocal rr_avg
        rr=pp-last_p; rr_avg=rr if rr_avg==0 else rr_avg+((rr-rr_avg)>>3)
    for n in range(N):
        e=int(env[n])
        if n<P.INIT:
            mx=max(mx,e); sm+=e
            if n==P.INIT-1: SPKI=mx>>2; NPKI=sm>>11
            continue
        e1=int(env[n-1]); e2=int(env[n-2])
        shift=2
        if mode=='ratio' and SPKI>0 and NPKI*p['d']>SPKI: shift=p['s']
        THR=NPKI+((SPKI-NPKI)>>shift) if SPKI>NPKI else NPKI
        if e1>e2 and e1>=e:
            pk=n-1; gap=pk-last_p; ok=(not have) or gap>=P.REFR
            if e1>THR and ok:
                if have and gap<P.TWAVE_GAP and e1<(last_pk>>1):
                    NPKI=NPKI-(NPKI>>3)+(e1>>3)
                else:
                    SPKI=SPKI-(SPKI>>3)+(e1>>3)
                    if have: upd(pk)
                    beats.append((pk,n)); last_p=pk; last_pk=e1; have=True; cand_ok=False
            elif e1<=THR:
                NPKI=NPKI-(NPKI>>3)+(e1>>3)
                if e1>(THR>>1) and ok and (not cand_ok or e1>cand_v): cand_v=e1; cand_i=pk; cand_ok=True
        if have and rr_avg!=0 and cand_ok and (n-last_p)>(rr_avg+(rr_avg>>1)+(rr_avg>>2)):
            SPKI=SPKI-(SPKI>>2)+(cand_v>>2); upd(cand_i); beats.append((cand_i,n)); last_p=cand_i; last_pk=cand_v; have=True; cand_ok=False
    return beats
print('  k | baseline FP/FN | est d=8,s=1 | est d=16,s=1 | est d=4,s=1')
for k in range(2,8):
    x=x0+((nz*k)>>3); hp=g.baseline_remove(x); bp=g.fir(hp,h); d=g.deriv(bp); sq,env=g.mwi(d)
    row=[]
    for mode,p in [('base',{}),('ratio',{'d':8,'s':1}),('ratio',{'d':16,'s':1}),('ratio',{'d':4,'s':1})]:
        b=decide2(env,mode,p); r=g.locate(hp,b); s=g.score(r,ref); row.append('%2d/%d'%(s['FP'],s['FN']))
    print('%3d | %10s | %11s | %12s | %10s'%(k,row[0],row[1],row[2],row[3]))
