"""Member B: baseline vs optimised design. (1) detection results over all noise levels (Python model, 100 s)
(2) hardware resources COUNTED from the RTL parameters (storage bits, multipliers) - NOT Quartus numbers."""
import numpy as np, sys
sys.path.insert(0,'python')
import golden as g
x0=np.load('sim/ecg.npy'); nz=np.load('sim/noise.npy'); h=list(np.load('python/fir_q12.npy'))
ref=[int(v) for v in open('data/ref_beats.txt').read().split()]
print('=== 1. Detection results, MIT-BIH record 100, 100 s (false beats / missed beats, R-peak error)')
print(' k | SNR(dB) |  baseline FP/FN  err(ms) | optimised FP/FN  err(ms) | same R-peak list?')
for k in range(8):
    x=x0+((nz*k)>>3); snr='clean' if k==0 else '%.1f'%(20*np.log10(np.std(x0-x0.mean())/np.std((nz*k)>>3)))
    b=g.run(x,h); o=g.run(x,h,W=12,sqshift=4,SW=18)
    sb=g.score(b['rpeaks'],ref); so=g.score(o['rpeaks'],ref)
    print('%2d | %7s |      %2d/%d      %5.1f   |      %2d/%d      %5.1f   | %s'%(k,snr,sb['FP'],sb['FN'],sb['abs_err_ms'],so['FP'],so['FN'],so['abs_err_ms'],'yes' if b['rpeaks']==o['rpeaks'] else 'no'))
N_TAPS=41
def count(DW,BLW,SQW,EW,mults):
    fir_sr=(N_TAPS-1 if mults==N_TAPS else N_TAPS)*DW
    parts=[('FIR shift register',fir_sr),('R-peak buffer (1024 x DW)',1024*DW),('Window buffer (54 x SQW)',54*SQW),('Window sum',EW),
           ('Baseline register',BLW),('Derivative history (4 x DW)',4*DW),('Decision registers (8 x EW + sum)',8*EW+EW+11)]
    return parts
base=count(16,24,32,40,41); opt=count(12,20,18,24,1)
print('\n=== 2. Resources counted from the RTL (NOT Quartus results)')
print('%-36s %10s %10s %8s'%('item','baseline','optimised','saving'))
tb=to=0
for (n,b),(_,o) in zip(base,opt):
    tb+=b; to+=o; print('%-36s %10d %10d %7.0f%%'%(n,b,o,100*(b-o)/b))
print('%-36s %10d %10d %7.0f%%'%('TOTAL register / memory bits',tb,to,100*(tb-to)/tb))
print('%-36s %10s %10s'%('FIR multipliers','41','1'))
print('%-36s %10s %10s'%('Clock cycles per sample (pipeline)','6','48'))
print('%-36s %10s %10s'%('Clock cycles, beat accepted -> BPM','97','97'))
print('Cycles available per sample on the board: 138889 (50 MHz / 360 Hz) -> worst case uses %.2f %%'%(100*97/138889))
