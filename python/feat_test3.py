import numpy as np, sys
sys.path.insert(0,'python')
import golden as g
x0=np.load('sim/ecg.npy'); nz=np.load('sim/noise.npy'); h=list(np.load('python/fir_q12.npy'))
ref=np.array([int(v) for v in open('data/ref_beats.txt').read().split()])
cache={}
def prep(k):
    if k not in cache:
        x=x0+((nz*k)>>3); hp=g.baseline_remove(x); bp=g.fir(hp,h); d=g.deriv(bp); sq,env=g.mwi(d)
        beats,_=g.decide(env); rp=g.locate(hp,beats); cache[k]=(d,env,beats,rp,hp)
    return cache[k]
def run(k,B,A,G):
    d,env,beats,rp,hp=prep(k); keep=[]; recentE=[]; rrs=[]; last=None
    for (p,n),r in zip(beats,rp):
        w=d[p-54:p+1]; mp=int(w.max()); mn=int(-w.min()); hi=max(mp,mn); bal=min(mp,mn)/hi if hi else 0
        gap=None if last is None else p-last
        rr=np.median(rrs[-8:]) if len(rrs)>=4 else None
        ea=np.mean(recentE[-8:]) if len(recentE)>=3 else None
        premature = gap is not None and rr is not None and gap<G*rr
        weak = ea is not None and env[p]<A*ea
        if premature and (bal<B or weak): continue
        keep.append(r); recentE.append(int(env[p]))
        if gap is not None: rrs.append(gap)
        last=p
    s=g.score(keep,ref); return s['FP'],s['FN']
print('rule: reject a PREMATURE beat (gap < G x median RR) if (balance<B or weak amplitude<A x recent mean)')
for B,A,G in [(0.5,0.8,0.8),(0.5,0.9,0.85),(0.6,0.9,0.85),(0.5,0.8,0.7),(0.5,1.0,0.9)]:
    out=[]
    for k in [0,2,3,4,5,7]:
        fp,fn=run(k,B,A,G); out.append('k%d:%d/%d'%(k,fp,fn))
    print('B=%.1f A=%.1f G=%.2f ->'%(B,A,G),'  '.join(out))
print('baseline          ->  k0:0/0  k2:1/0  k3:4/0  k4:8/0  k5:11/0  k7:11/0')
