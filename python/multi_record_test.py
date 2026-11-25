import sys,os,numpy as np,wfdb,warnings
warnings.filterwarnings('ignore')
sys.path.insert(0,'python')
import golden as g, noise
h=list(np.load('python/fir_q12.npy'))
N=36000
recs=sorted({f[:3] for f in os.listdir('data/mitdb') if f.endswith('.dat')})
BEAT=set("NLRBAaJSVrFejnE/fQ")
rows=[]
for r in recs:
    rec=wfdb.rdrecord('data/mitdb/'+r,physical=False); ann=wfdb.rdann('data/mitdb/'+r,'atr')
    x=rec.d_signal[:,0].astype(np.int64)-1024; x=x[:N]
    clip=int((x.min()<-2048)|(x.max()>2047))
    ref=[int(s) for s,c in zip(ann.sample,ann.symbol) if c in BEAT and s<N]
    nz=noise.make_noise(N,seed=7); nz=nz/np.std(nz)*(2.0*np.std(x-x.mean())); nz=np.clip(np.round(nz),-2047,2047).astype(np.int64)
    out={'rec':r,'lead':rec.sig_name[0],'nref':len([v for v in ref if v>=1080])}
    for k in (0,4):
        xx=g.sat(x+((nz*k)>>3),12); m=g.run(xx,h)
        s=g.score(m['rpeaks'],ref); out[k]=s
    out['clip']=clip; rows.append(out)
    print(r,out['lead'],out['nref'],'k0 Se %.2f PPV %.2f | k4 Se %.2f PPV %.2f'%(out[0]['Se'],out[0]['PPV'],out[4]['Se'],out[4]['PPV']),'CLIP' if clip else '',flush=True)
import pickle; pickle.dump(rows,open('results/multi_record_rows.pkl','wb'))
