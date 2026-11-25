"""Draw GTKWave-style waveform pictures straight from the Icarus VCD files."""
import re, sys, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
SIGNED={'ecg_in','baseline_removed','filtered','derivative'}
WID={}
def read_vcd(path):
    ids={}; width={}; ch={}; t=0
    with open(path) as f:
        for line in f:
            line=line.strip()
            if not line: continue
            if line.startswith('$var'):
                p=line.split(); ids[p[3]]=p[4]; width[p[4]]=int(p[2]); ch[p[4]]=[]; continue
            if line[0]=='#': t=int(line[1:]); continue
            if line[0] in 'bB':
                v,i=line[1:].split(); name=ids.get(i)
                if name: ch[name].append((t,v))
            elif line[0] in '01xXzZ' and line[1:] in ids:
                ch[ids[line[1:]]].append((t,line[0]))
    WID.update(width)
    return ch,width
def val(v,name):
    if set(v)<=set('01'):
        v=v.rjust(WID.get(name,len(v)),'0')
        n=int(v,2)
        if name in SIGNED and n>=1<<(len(v)-1): n-= 1<<len(v)
        return n
    return None
def at(ch,name,t):
    cur=ch[name][0][1] if ch[name] else '0'
    for tt,v in ch[name]:
        if tt<=t: cur=v
        else: break
    return cur
# ---------- overview (analog) ----------
def overview(vcd,out,div=100):
    ch,w=read_vcd(vcd)
    ps_per_ms=1e9; tms=lambda t:t/1e9    # VCD time unit is 1 ps
    fig,axs=plt.subplots(6,1,figsize=(13,8.6),dpi=150,sharex=True)
    def analog(ax,name,color,label):
        pts=[(tms(t),val(v,name)) for t,v in ch[name] if val(v,name) is not None]
        x=[p[0] for p in pts]; y=[p[1] for p in pts]; ax.step(x,y,where='post',color=color,lw=.8); ax.set_ylabel(label,fontsize=8,rotation=0,ha='right',va='center')
    analog(axs[0],'ecg_in','#1F3864','ecg_in'); analog(axs[1],'filtered','#2E75B6','filtered'); analog(axs[2],'envelope','#C55A11','envelope')
    for name,ax,label,col in [('peak_found',axs[3],'peak_found','#7F7F7F'),('beat_pulse',axs[4],'beat_pulse','#C00000')]:
        pts=[(tms(t),int(v)) for t,v in ch[name] if v in '01']; x=[p[0] for p in pts]; y=[p[1] for p in pts]
        ax.step(x,y,where='post',color=col,lw=1.2); ax.set_ylim(-0.2,1.3); ax.set_yticks([0,1]); ax.set_ylabel(label,fontsize=8,rotation=0,ha='right',va='center')
    pts=[(tms(t),val(v,'bpm')) for t,v in ch['bpm'] if val(v,'bpm') is not None]
    axs[5].step([p[0] for p in pts],[p[1] for p in pts],where='post',color='#3B7D23',lw=1.3); axs[5].set_ylabel('bpm',fontsize=8,rotation=0,ha='right',va='center'); axs[5].set_ylim(0,130)
    for a in axs: a.grid(alpha=.25)
    ms_per_ecg_s=360*div*20e-6        # simulated ms per ECG second
    axs[5].set_xlabel('simulation time (ms)        [ %.2f ms of simulation = 1 s of ECG ]'%ms_per_ecg_s)
    sec=axs[0].secondary_xaxis('top',functions=(lambda x:x/ms_per_ecg_s,lambda x:x*ms_per_ecg_s)); sec.set_xlabel('ECG time (s)')
    axs[0].set_title('Simulation waveform (Icarus Verilog -> GTKWave data): 10 s of MIT-BIH record 100',fontsize=10,fontweight='bold',pad=34)
    plt.tight_layout(); plt.savefig(out); plt.close()
# ---------- GTKWave-style digital view ----------
LBL={'beat_pulse':'rpeak_valid','rpeak_index':'rpeak_idx'}
def gtk_view(vcd,out,t0,t1,signals,title,unit_ns=True):
    ch,w=read_vcd(vcd)
    BG='#000000'; G='#00FF00'; fig,ax=plt.subplots(figsize=(13,0.46*len(signals)+1.0),dpi=150); fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    n=len(signals); ax.set_xlim(t0,t1); ax.set_ylim(-0.5,n)
    for r,name in enumerate(signals):
        y0=n-1-r
        if name.startswith('#'):
            ax.text(t0+0.005*(t1-t0),y0+0.45,name[1:],color='#00E5FF',fontsize=9,fontweight='bold',va='center'); ax.axhline(y0+0.95,color='#555555',lw=.6); continue
        wd=w[name]; ev=[(t,v) for t,v in ch[name]]
        first=at(ch,name,t0); cur=first; seg=[(t0,first)]+[(t,v) for t,v in ev if t0<t<=t1]
        if wd==1:
            xs=[];ys=[]
            for i,(t,v) in enumerate(seg):
                lv={'1':0.8,'0':0.1}.get(v,0.45)
                if i>0: xs.append(t); ys.append(ys[-1])
                xs.append(t); ys.append(lv)
            xs.append(t1); ys.append(ys[-1])
            ax.plot(xs,[y0+q*0.8 for q in ys],color=G,lw=1.0)
        else:
            for i,(t,v) in enumerate(seg):
                te=seg[i+1][0] if i+1<len(seg) else t1
                d=min(0.025*(t1-t0),(te-t)/3); xa,xb=t,te
                top=y0+0.8; bot=y0+0.1; mid=y0+0.45
                if xb-xa<=0: continue
                pts=[(xa,mid),(xa+d,top),(xb-d,top),(xb,mid),(xb-d,bot),(xa+d,bot)]
                ax.add_patch(Polygon(pts,closed=True,fill=False,ec=G,lw=0.9))
                vv=val(v,name); label='x' if vv is None else str(vv)
                px=(xb-xa)/(t1-t0)*13*150
                if px>len(label)*7.5+10: ax.text((xa+xb)/2,mid,label,color='#E0E000',fontsize=7.5,ha='center',va='center')
    ax.set_yticks([n-1-r+0.45 for r in range(n)]); ax.set_yticklabels([('' if s.startswith('#') else ('%s[%d:0]'%(LBL.get(s,s),w[s]-1) if w[s]>1 else LBL.get(s,s))) for s in signals],color='white',fontsize=8.5)
    sc=1000.0 if unit_ns else 1e9
    ticks=np.linspace(t0,t1,9); ax.set_xticks(ticks); ax.set_xticklabels([('%.0f ns'%((x-t0)/sc)) if unit_ns else ('%.1f ms'%((x-t0)/sc)) for x in ticks],color='white',fontsize=8)
    ax.tick_params(colors='white'); ax.grid(axis='x',color='#333333',lw=.5)
    for s in ax.spines.values(): s.set_color('#555555')
    ax.set_title(title,color='white',fontsize=10,fontweight='bold')
    plt.tight_layout(); plt.savefig(out,facecolor=BG); plt.close()
if __name__=='__main__':
    overview('sim/demo_overview.vcd','results/waveform_overview.png')
    ch,w=read_vcd('sim/demo_zoom.vcd')
    sv=[t for t,v in ch['sample_valid'] if v=='1']; ts=sv[0]
    names=['clk','rst','sw','sample_valid','ecg_in','baseline_valid','baseline_removed','filtered_valid','filtered','deriv_valid','derivative','envelope_valid','envelope','peak_found']
    gtk_view('sim/demo_zoom.vcd','results/waveform_zoom_pipeline.png',ts-20000,ts+300000,names,'Zoom 1: one ECG sample ripples through the pipeline, one clock (20 ns) per stage')
    ts2=sv[1]; bp=[t for t,v in ch['beat_pulse'] if v=='1'][0]
    names2=['clk','sample_valid','peak_found','beat_pulse','rpeak_index','bpm_valid','rr_samples','bpm']
    gtk_view('sim/demo_zoom.vcd','results/waveform_zoom_beat.png',ts2-20000,ts2+2300000,names2,'Zoom 2: beat accepted -> R-peak located (scan) -> RR and BPM computed by the hardware divider')
        # ---- port-order pictures: INPUT PORTS first, then OUTPUT PORTS ----
    P=['#INPUT PORTS','clk','rst','sw','#OUTPUT PORTS','done','beat_pulse','rpeak_index','rr_samples','bpm_valid','bpm']
    gtk_view('sim/demo_zoom.vcd','results/waveform_ports_zoom.png',ts2-20000,ts2+2300000,P,'Top-level ports in order: inputs first, then outputs (zoom on one heartbeat)')
    chO,wO=read_vcd('sim/demo_overview.vcd')
    tend=max(t for n in chO for t,_ in chO[n])
    gtk_view('sim/demo_overview.vcd','results/waveform_ports_overview.png',0,tend,[x for x in P if x!='clk'],'Top-level ports over the whole run: 7.3 ms of simulation = 10 s of ECG (sped up), clk omitted as too dense',unit_ns=False)
    print('ts',ts,'beat',bp)
