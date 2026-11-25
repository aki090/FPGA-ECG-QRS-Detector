import numpy as np, sys
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ref=np.array([int(v) for v in open('data/ref_beats.txt').read().split()])
A,B=7200,10080   # 8 s window
fig,axs=plt.subplots(4,2,figsize=(13,8.5),dpi=150,sharex='col')
for c,(k,title) in enumerate([(0,'Clean ECG (SW = 0)'),(4,'Noisy ECG, SNR = 0 dB (SW = 4)')]):
    d='results/k%d'%k; L=lambda f:np.loadtxt('%s/%s.txt'%(d,f),dtype=np.int64)
    x,bp,env=L('x'),L('bp'),L('env'); rp=L('rpeaks'); t=np.arange(len(x))/360
    sl=slice(A,B); ts=t[sl]
    axs[0,c].plot(ts,x[sl],lw=.7,color='#1F3864'); axs[0,c].set_title(title,fontsize=10,fontweight='bold')
    axs[1,c].plot(ts,bp[sl],lw=.7,color='#2E75B6')
    axs[2,c].plot(ts,env[sl],lw=.9,color='#C55A11')
    axs[3,c].plot(ts,x[sl],lw=.7,color='#7F7F7F')
    r=rp[(rp>=A)&(rp<B)]; a=ref[(ref>=A)&(ref<B)]
    axs[3,c].plot(r/360,x[r],'rv',ms=7,label='RTL detected R-peak')
    axs[3,c].plot(a/360,x[a]*0+x[sl].min()-8,'g^',ms=5,label='annotation')
    axs[3,c].legend(loc='upper right',fontsize=7); axs[3,c].set_xlabel('time (s)')
for r,lab in enumerate(['1  ECG input (after noise injector)','2  After FIR band-pass','3  Integrated signal (envelope)','4  Detected R-peaks']): axs[r,0].set_ylabel(lab,fontsize=8)
for ax in axs.flat: ax.grid(alpha=.25)
plt.tight_layout(); plt.savefig('results/stage_waveforms.png'); print('ok')
