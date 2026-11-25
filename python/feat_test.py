import numpy as np, sys
sys.path.insert(0,'python')
import golden as g
x0=np.load('sim/ecg.npy'); nz=np.load('sim/noise.npy'); h=list(np.load('python/fir_q12.npy'))
ref=np.array([int(v) for v in open('data/ref_beats.txt').read().split()])
k=5
x=x0+((nz*k)>>3); hp=g.baseline_remove(x); bp=g.fir(hp,h); d=g.deriv(bp); sq,env=g.mwi(d)
beats,_=g.decide(env); rp=np.array(g.locate(hp,beats))
tp=[];fp=[]
for (p,n),r in zip(beats,rp):
    if r<1080: continue
    (tp if np.min(abs(ref-r))<=54 else fp).append((p,r))
def feats(p):
    w=d[p-54:p+1]                       # derivative over the 150 ms window ending at the envelope peak
    mp=int(w.max()); mn=int(-w.min()); lo,hi=min(mp,mn),max(mp,mn)
    ww=bp[p-54:p+1]; 
    return dict(bal=lo/hi if hi else 0, mp=mp, mn=mn, env=int(env[p]), rng=int(ww.max()-ww.min()))
import statistics as st
for name,L in [('TRUE beats',tp),('FALSE beats',fp)]:
    F=[feats(p) for p,r in L]
    print(name,len(L),'| balance min/median/max: %.2f %.2f %.2f'%(min(f['bal'] for f in F),st.median(f['bal'] for f in F),max(f['bal'] for f in F)),
          '| env median %d | bp range median %d'%(st.median(f['env'] for f in F),st.median(f['rng'] for f in F)))
print('false beat balances:',sorted(round(feats(p)['bal'],2) for p,r in fp))
print('true beat balances (lowest 8):',sorted(round(feats(p)['bal'],2) for p,r in tp)[:8])
