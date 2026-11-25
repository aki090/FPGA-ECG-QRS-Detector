"""Member B, week 2: how many bits does each stage really need? Which narrower designs keep the detections identical?"""
import numpy as np, sys
sys.path.insert(0,'python')
import golden as g
P=g.P
x0=np.load('sim/ecg.npy'); nz=np.load('sim/noise.npy'); hq12=np.load('python/fir_q12.npy')
ref=[int(v) for v in open('data/ref_beats.txt').read().split()]
KS=[0,2,4,5,7]
def sbits(m): return int(m).bit_length()+1          # signed bits to hold +-m
def ubits(m): return int(m).bit_length()
def run(k,Q=12,sqshift=0,inshift=0):
    x=(x0+((nz*k)>>3))>>inshift
    h=[int(round(c/4096*(1<<Q))) for c in hq12]
    hp=g.baseline_remove(x); acc=np.convolve(hp,np.array(h,dtype=np.int64))[:len(hp)]
    bp=np.clip(acc>>Q,-32768,32767); d=g.deriv(bp); sq=(d*d)>>sqshift
    c=np.cumsum(sq); env=c.copy(); env[P.MWI:]=c[P.MWI:]-c[:-P.MWI]
    beats,_=g.decide(env); r=g.locate(hp,beats)
    return dict(x=x,hp=hp,bp=bp,d=d,sq=sq,env=env,r=r)
# 1) observed ranges
mx={s:0 for s in ['x','hp','bp','d','sq','env']}
base={}
for k in KS:
    b=run(k); base[k]=b
    for s in mx: mx[s]=max(mx[s],int(np.max(np.abs(b[s]))))
print('--- Observed value ranges (record 100, 100 s, noise levels k=%s)'%KS)
print('%-34s %10s %12s %12s'%('signal','max |value|','bits needed','RTL width now'))
rows=[('x  ecg after noise injector','x',sbits,16),('hp baseline-removed','hp',sbits,16),('bp FIR output','bp',sbits,16),
      ('d  derivative','d',sbits,16),('sq squared (unsigned)','sq',ubits,32),('env 54-sample sum (unsigned)','env',ubits,40)]
for name,key,f,now in rows: print('%-34s %10d %12d %12d'%(name,mx[key],f(mx[key]),now))
# 2) variants: identical detections?
print('\n--- Narrower designs: do detections stay identical to the baseline? (FP/FN vs annotations)')
variants=[('baseline (Q12, full)',dict()),('FIR coeffs Q10',dict(Q=10)),('FIR coeffs Q8',dict(Q=8)),('FIR coeffs Q7',dict(Q=7)),('FIR coeffs Q6',dict(Q=6)),
 ('square >> 4',dict(sqshift=4)),('square >> 8',dict(sqshift=8)),('square >> 10',dict(sqshift=10)),('input drop 1 LSB',dict(inshift=1)),('input drop 2 LSB',dict(inshift=2)),
 ('Q8 + square>>8 + drop 1 LSB',dict(Q=8,sqshift=8,inshift=1))]
print('%-30s'%'design'+''.join('  k=%d same/FP/FN'%k for k in KS))
for name,kw in variants:
    line='%-30s'%name
    for k in KS:
        r=run(k,**kw); same=(r['r']==base[k]['r']); s=g.score(r['r'],ref)
        line+='  %5s %2d/%-2d    '%('YES' if same else 'no',s['FP'],s['FN'])
    print(line)
