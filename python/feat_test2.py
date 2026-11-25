import numpy as np, sys
sys.path.insert(0,'python')
import golden as g
x0=np.load('sim/ecg.npy'); nz=np.load('sim/noise.npy'); h=list(np.load('python/fir_q12.npy'))
ref=np.array([int(v) for v in open('data/ref_beats.txt').read().split()])
def run(k,bal_thr,amp_thr):
    x=x0+((nz*k)>>3); hp=g.baseline_remove(x); bp=g.fir(hp,h); d=g.deriv(bp); sq,env=g.mwi(d)
    beats,_=g.decide(env); rp=g.locate(hp,beats)
    keep=[]; recent=[]
    for (p,n),r in zip(beats,rp):
        w=d[p-54:p+1]; mp=int(w.max()); mn=int(-w.min()); hi=max(mp,mn); bal=min(mp,mn)/hi if hi else 0
        ref_amp=int(np.mean(recent[-8:])) if len(recent)>=3 else None
        reject = bal<bal_thr and (ref_amp is None or env[p]<amp_thr*ref_amp)
        if reject: continue
        keep.append(r); recent.append(int(env[p]))
    s=g.score(keep,ref); return s['FP'],s['FN'],s['PPV'],s['Se']
print('rule: reject if balance<B and envelope< A x (mean of last 8 accepted)')
for B,A in [(0.5,1.0),(0.5,0.9),(0.5,0.8),(0.45,0.9),(0.4,1.0)]:
    out=[]
    for k in [0,2,3,4,5,7]:
        fp,fn,ppv,se=run(k,B,A); out.append('k%d:%d/%d'%(k,fp,fn))
    print('B=%.2f A=%.1f  FP/FN ->'%(B,A),'  '.join(out))
print('baseline FP/FN  ->  k0:0/0  k2:1/0  k3:4/0  k4:8/0  k5:11/0  k7:11/0')
