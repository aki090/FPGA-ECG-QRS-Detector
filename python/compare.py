"""Compare RTL simulation logs with the bit-accurate Python model, then score against annotations.
usage: python3 python/compare.py <outdir> <k>"""
import numpy as np, sys
sys.path.insert(0,'python')
import golden as g
out=sys.argv[1]; k=int(sys.argv[2])
W=int(sys.argv[3]) if len(sys.argv)>3 else 16; SQSH=int(sys.argv[4]) if len(sys.argv)>4 else 0; SW=int(sys.argv[5]) if len(sys.argv)>5 else 32
NS=int(sys.argv[6]) if len(sys.argv)>6 else 0
x0=np.load('sim/ecg.npy'); nz=np.load('sim/noise.npy'); h=list(np.load('python/fir_q12.npy'))
if NS: x0=x0[:NS]; nz=nz[:NS]
x=x0+((nz*k)>>3)
m=g.run(x,h,W,SQSH,SW)
x=g.sat(x,W)
ld=lambda f:np.loadtxt('%s/%s.txt'%(out,f),dtype=np.int64,ndmin=1)
ok=True
print('--- Stage-by-stage check: RTL (Verilog) vs Python golden model')
for name,key in [('x (after noise injector)',None),('hp (baseline removed)','hp'),('bp (FIR band-pass)','bp'),('d (derivative)','d'),('env (integrated)','env')]:
    a=ld({'x (after noise injector)':'x','hp (baseline removed)':'hp','bp (FIR band-pass)':'bp','d (derivative)':'d','env (integrated)':'env'}[name])
    b=x if key is None else m[key]
    same=len(a)==len(b) and np.array_equal(a,b)
    print('  %-26s %6d samples  %s'%(name,len(a),'MATCH (bit-exact)' if same else 'MISMATCH'))
    ok&=same
det=ld('det'); rp=ld('rpeaks')
gdet=np.array([b[0] for b in m['beats']]); grp=np.array(m['rpeaks'])
print('  %-26s %6d beats    %s'%('envelope peaks (det)',len(det),'MATCH' if np.array_equal(det,gdet) else 'MISMATCH')); ok&=np.array_equal(det,gdet)
print('  %-26s %6d beats    %s'%('R-peak positions',len(rp),'MATCH' if np.array_equal(rp,grp) else 'MISMATCH')); ok&=np.array_equal(rp,grp)
bp=np.loadtxt(out+'/bpm.txt',dtype=np.int64,ndmin=2)
exp=np.array([21600//r for r in np.diff(grp)])
bm=len(bp)==len(exp) and np.array_equal(bp[:,1],exp)
print('  %-26s %6d values   %s'%('BPM (hardware divider)',len(bp),'MATCH' if bm else 'MISMATCH')); ok&=bm
print('RESULT: RTL == golden model :',ok)
ref=[int(v) for v in open('data/ref_beats.txt').read().split() if not NS or int(v)<NS]
s=g.score(list(rp),ref)
print('\n--- Detection accuracy vs MIT-BIH annotations (tolerance +-150 ms, first 3 s excluded)')
print('  noise level k=%d : TP=%d FP=%d FN=%d | Sensitivity %.2f %% | PPV %.2f %% | F1 %.2f %% | mean |R-peak error| %.1f ms'%(k,s['TP'],s['FP'],s['FN'],s['Se'],s['PPV'],s['F1'],s['abs_err_ms']))
print('  heart rate: mean %.1f BPM (annotation mean %.1f BPM)'%(bp[:,1].mean(), 21600/np.mean(np.diff([r for r in ref if r>=1080]))))
