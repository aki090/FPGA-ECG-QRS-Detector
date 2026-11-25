import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams['font.family']='Liberation Sans'
NAVY='#1F3864'; LB='#DCE6F4'; ORG='#FBD9A8'; GRN='#DDEFD8'; GRY='#EDEDED'
fig,ax=plt.subplots(figsize=(14.5,7.2),dpi=170); ax.set_xlim(0,31); ax.set_ylim(0,14.4); ax.axis('off')
def box(x,y,w,h,t1,t2,fc=LB,ec=NAVY,fs=8.6):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.02,rounding_size=0.15",fc=fc,ec=ec,lw=1.4))
    ax.text(x+w/2,y+h-0.35,t1,ha='center',va='top',fontsize=fs,fontweight='bold',color=NAVY)
    ax.text(x+w/2,y+h-1.05,t2,ha='center',va='top',fontsize=7,linespacing=1.3,color='#222')
def arr(p,q,lab=None,above=True,ls='-',lx=0,ly=0):
    ax.add_patch(FancyArrowPatch(p,q,arrowstyle='-|>',mutation_scale=10,color='black',lw=1.2,ls=ls,shrinkA=0,shrinkB=0))
    if lab: ax.text((p[0]+q[0])/2+lx,(p[1]+q[1])/2+ly+(0.2 if above else -0.2),lab,ha='center',va='bottom' if above else 'top',fontsize=6.1,linespacing=1.15,color='#7F2B0B')
ax.text(0.2,14.0,'Simulation set-up: testbench + design hierarchy (Verilog modules and the signals between them)',fontsize=11.5,fontweight='bold',color=NAVY,va='center')
# testbench
box(0.3,5.2,4.4,6.2,'tb_demo.v','TESTBENCH\n(not hardware)\n\nclk  50 MHz  (always #10)\nrst  (reset, then released)\nsw[2:0]  noise level\n\nprints heartbeats\non the console\nwrites .vcd file\nfor GTKWave',fc=GRY,ec='#595959')
ax.add_patch(FancyBboxPatch((5.4,0.6),25.0,12.4,boxstyle="round,pad=0.02,rounding_size=0.2",fc='#F8FAFD',ec=NAVY,lw=1.6,ls='--'))
ax.text(17.9,12.6,'DUT = ecg_qrs_top  (the design under test)',ha='center',fontsize=9.5,fontweight='bold',color=NAVY)
arr((4.7,9.9),(5.4,9.9),'clk, rst,\nsw',lx=0.0)
bw,bh=3.0,2.6; X=[5.9,10.9,15.9,20.9,25.9]; Y1=8.7; Y2=3.4
r1=[('sample_source','ECG ROM + noise ROM\n1 sample every\nSAMPLE_DIV clocks',GRY),('noise_injector','y = ecg + (noise x k)/8\nk = sw[2:0]',ORG),('baseline_remove','IIR baseline estimate\nsubtracted',LB),('fir_bp','41-tap FIR\nband-pass 5-20 Hz',LB),('derivative','5-point derivative',LB)]
for x,(a,b,c) in zip(X,r1): box(x,Y1,bw,bh,a,b,fc=c)
labs=['valid\necg[11:0]\nnoise[11:0]','x_v\nx[15:0]','hp_v\nhp[15:0]','bp_v\nbp[15:0]']
for i in range(4): arr((X[i]+bw,Y1+1.3),(X[i+1],Y1+1.3),labs[i])
r2=[('squarer','d x d',LB),('mwi','150 ms running sum\n(54 samples)',LB),('qrs_decision','peak detect, adaptive\nthreshold, refractory,\nsearch-back',ORG),('rpeak_locator','finds true R-peak\nin stored ECG',ORG),('rr_bpm','RR interval\nBPM = 21600 / RR',GRN)]
Xr=[25.9,20.9,15.9,10.9,5.9]
for x,(a,b,c) in zip(Xr,r2): box(x,Y2,bw,bh,a,b,fc=c)
arr((X[4]+bw/2,Y1),(Xr[0]+bw/2,Y2+bh)); ax.text(X[4]+bw/2+0.25,6.9,'d_v, d[15:0]',fontsize=6.1,color='#7F2B0B',va='center')
for i,l in enumerate(['sq_v\nsq[31:0]','env_v\nenv[39:0]','det_v\ndet_p[31:0]','rpeak_valid\nrpeak_idx[31:0]']):
    arr((Xr[i],Y2+1.3),(Xr[i+1]+bw,Y2+1.3),l)
# hp to locator
ax.plot([X[2]+bw/2,X[2]+bw/2],[Y1,6.9],color='#555',lw=1.1,ls='--'); ax.plot([X[2]+bw/2,Xr[3]+bw/2],[6.9,6.9],color='#555',lw=1.1,ls='--')
arr((Xr[3]+bw/2,6.9),(Xr[3]+bw/2,Y2+bh),None,ls='--')
ax.text(15.0,7.05,'hp[15:0]  (buffered ECG for R-peak search)',fontsize=6.6,color='#555',ha='center',va='bottom')
# outputs
box(5.9,0.95,15.0,1.6,'Outputs seen by the testbench','beat_pulse (1 per heartbeat)    rpeak_index[31:0]    rr_samples[15:0]    bpm[15:0]    bpm_valid',fc=GRN,ec='#3B7D23',fs=8.2)
arr((Xr[4]+bw/2,Y2),(Xr[4]+bw/2,2.55)); ax.text(Xr[4]+bw/2+0.25,2.95,'rr, bpm, bpm_valid',fontsize=6.1,color='#7F2B0B',va='center')
ax.text(5.9,0.35,'clk and rst go to every module (not drawn to keep the picture clear).  Orange = our contributions,  green = outputs,  grey = memory / testbench.',fontsize=7,color='#444',va='center')
plt.savefig('results/rtl_hierarchy.png',bbox_inches='tight',pad_inches=0.1,facecolor='white')
