"""Summarise the noise sweep (k = 0..7): RTL-vs-model match + detection accuracy; draw the accuracy-vs-SNR plot."""
import numpy as np, sys, os
sys.path.insert(0,'python')
import golden as g
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
x0=np.load('sim/ecg.npy'); nz=np.load('sim/noise.npy'); h=list(np.load('python/fir_q12.npy'))
ref=[int(v) for v in open('data/ref_beats.txt').read().split()]
rows=[]
print(' k |  SNR(dB) | RTL==model | beats | TP  FP  FN |   Se %   PPV %    F1 % | R-peak err (ms)')
for k in range(8):
    d='results/k%d'%k
    if not os.path.exists(d+'/rpeaks.txt'): continue
    x=x0+((nz*k)>>3); m=g.run(x,h)
    rp=np.loadtxt(d+'/rpeaks.txt',dtype=np.int64,ndmin=1)
    same=np.array_equal(rp,np.array(m['rpeaks'])) and np.array_equal(np.loadtxt(d+'/env.txt',dtype=np.int64),m['env'])
    s=g.score(list(rp),ref)
    snr=float('inf') if k==0 else 20*np.log10(np.std(x0-x0.mean())/np.std((nz*k)>>3))
    rows.append((k,snr,s))
    print('%2d | %8s | %-10s | %5d | %3d %3d %3d | %6.2f %6.2f %6.2f | %5.1f'%(k,'clean' if k==0 else '%.1f'%snr,'YES' if same else 'NO',len(rp),s['TP'],s['FP'],s['FN'],s['Se'],s['PPV'],s['F1'],s['abs_err_ms']))
ks=[r[0] for r in rows]; lab=['clean' if r[0]==0 else '%.0f'%r[1] for r in rows]
fig,ax=plt.subplots(figsize=(7,3.8),dpi=170)
ax.plot(range(len(rows)),[r[2]['Se'] for r in rows],'o-',label='Sensitivity',color='#1F3864')
ax.plot(range(len(rows)),[r[2]['PPV'] for r in rows],'s--',label='PPV',color='#C55A11')
ax.set_xticks(range(len(rows))); ax.set_xticklabels(lab); ax.set_xlabel('SNR (dB)  – set by SW[2:0] noise level'); ax.set_ylabel('%')
ax.set_ylim(80,101); ax.grid(alpha=.3); ax.legend(); ax.set_title('RTL simulation: detection accuracy vs injected noise (MIT-BIH record 100, 100 s)',fontsize=9)
plt.tight_layout(); plt.savefig('results/accuracy_vs_noise.png'); print('saved results/accuracy_vs_noise.png')
