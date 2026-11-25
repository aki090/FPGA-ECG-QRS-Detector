"""Synthetic NST-like noise (baseline wander + muscle artefact + electrode motion). Integer ADC units."""
import numpy as np
from scipy.signal import butter, lfilter
FS=360
def make_noise(n,seed=1,mix=(1/3,1/3,1/3)):
    rng=np.random.default_rng(seed); t=np.arange(n)/FS
    bw=sum(a*np.sin(2*np.pi*f*t+ph) for a,f,ph in [(1.0,0.15,0.3),(0.6,0.33,1.7),(0.4,0.5,4.0)])
    wn=rng.standard_normal(n); b,a=butter(2,[25/(FS/2),0.99],btype='band')   # muscle: high-frequency noise
    env=1+0.8*np.sin(2*np.pi*0.2*t+1.0)**2                                   # bursty amplitude
    ma=lfilter(b,a,wn)*env
    em=np.zeros(n)                                                           # electrode motion: random decaying steps
    pos=rng.integers(0,n,size=max(1,n//(FS*6)))
    for p in pos:
        L=min(n-p,int(FS*0.6)); em[p:p+L]+=rng.choice([-1,1])*np.exp(-np.arange(L)/(0.15*FS))*rng.uniform(0.7,1.3)
    nz=lambda v:v/np.std(v)
    return mix[0]*nz(bw)+mix[1]*nz(ma)+mix[2]*nz(em)
def add_noise(x,snr_db,seed=1,mix=(1/3,1/3,1/3)):
    nz=make_noise(len(x),seed,mix); nz=nz/np.std(nz)
    sig=np.std(x-np.mean(x)); amp=sig/(10**(snr_db/20))
    return np.round(x+amp*nz).astype(np.int64)
