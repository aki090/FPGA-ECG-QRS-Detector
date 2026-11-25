"""One-page top-level ports diagram (main ports only: no real-time counters, no debug taps)."""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
plt.rcParams['font.family']=['Liberation Sans','DejaVu Sans']
NAVY='#1F3864'; BLUE='#2E5E9E'; ORG='#B5470B'; GRY='#4B5563'
W,H=2000,1414
fig=plt.figure(figsize=(20,14.14),dpi=165); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(H,0); ax.axis('off')
def box(x0,y0,x1,y1,fc,ec,lw=2.5,ls='-',r=14):
    ax.add_patch(FancyBboxPatch((x0,y0),x1-x0,y1-y0,boxstyle=f"round,pad=0,rounding_size={r}",fc=fc,ec=ec,lw=lw,ls=ls))
def T(x,y,s,fs=11.5,c='#111',w='normal',ha='left',st='normal'): ax.text(x,y,s,fontsize=fs,color=c,fontweight=w,ha=ha,va='center',style=st)
def arrow(p,q,c='black',ls='-',lw=2.2):
    ax.add_patch(FancyArrowPatch(p,q,arrowstyle='-|>',mutation_scale=16,color=c,lw=lw,ls=ls,shrinkA=0,shrinkB=0))
def line(xs,ys,c='black',ls='-',lw=2.2): ax.plot(xs,ys,color=c,ls=ls,lw=lw,solid_capstyle='butt')
def dot(x,y,n,c=ORG):
    ax.add_patch(Circle((x,y),19,fc=c,ec='white',lw=1.5,zorder=5)); ax.text(x,y,str(n),color='white',fontsize=11,fontweight='bold',ha='center',va='center',zorder=6)
T(25,40,'ECG QRS detector: top-level ports and the full signal flow',26,NAVY,'bold')
T(25,80,'Read the picture left to right, then the second row. Inputs are on the left, the main outputs on the right. Numbered arrows are internal signals between modules (table at the bottom).',10.3,'#444')
T(25,104,'On the DE1-SoC the same detector sits inside de1soc_top: inputs CLOCK_50, KEY[3:0], SW[9:0]; outputs LEDR[9:0], HEX0 to HEX5 [6:0].',10.3,'#444')
# input ports
box(23,140,293,550,'#FDF1E3',ORG)
T(158,160,'INPUT PORTS',14,ORG,'bold','center'); T(158,195,'(driven by the testbench / board)',10.3,'#555','normal','center','italic')
for y,n,d in [(260,'clk','1 bit:  50 MHz clock, 20 ns'),(347,'rst','1 bit:  reset, high = reset'),(435,'sw [2:0]','3 bits:  noise level 0 to 7')]:
    T(42,y,n,13,BLUE,'bold'); T(42,y+28,d,10.5)
T(42,503,'clk and rst go to every module',9.6,'#555','normal','left','italic')
arrow((293,341),(323,341),c=BLUE,lw=2.6)
# parameters
box(23,590,293,983,'white','#9CA3AF',2)
T(158,610,'PARAMETERS',14,NAVY,'bold','center'); T(158,640,'baseline / optimised',10.3,'#555','normal','center','italic')
rows=[('N_SAMPLES','36000'),('SAMPLE_DIV','138889 (board)'),('DW  data width','16 / 12'),('BLW','24 / 20'),('SEQ  FIR type','0 / 1'),('ACCW','48 / 32'),('SQSH','0 / 4'),('SQW','32 / 18'),('EW  envelope','40 / 24')]
for i,(a,b) in enumerate(rows):
    y=681+i*30.8; T(38,y,a,10.8); T(279,y,b,10.8,ORG,'bold','right')
T(38,956,'SEQ = 1: one shared multiplier',9.6,'#555','normal','left','italic')
# top module frame
box(323,131,1660,983,'#F7F9FC',NAVY,3,(0,(6,4)),r=16)
T(990,155,'ecg_qrs_top   (the top module: everything inside this frame)',15,NAVY,'bold','center')
def mod(x,y,name,sub,lines,green=False):
    box(x,y,x+233,y+327,'#E2EFDA' if green else '#DCE6F4',NAVY,2.6,r=12)
    T(x+116,y+24,name,15,NAVY,'bold','center'); T(x+116,y+52,sub,9.8,'#444','normal','center','italic')
    for i,l in enumerate(lines):
        yy=y+84+i*21.4
        if l[0] in('IN','OUT'):
            T(x+14,yy,l[0],11,BLUE if l[0]=='IN' else ORG,'bold'); T(x+58,yy,l[1],11)
        else: T(x+58,yy,l[1],11)
X=[340,606,873,1140,1406]; Y1,Y2=198,614
mod(X[0],Y1,'sample_source','ECG + noise memory, timer',[('IN','clk, rst'),('OUT','valid'),('OUT','ecg [11:0]'),('OUT','noise [11:0]'),('OUT','done')],True)
mod(X[1],Y1,'noise_injector','adds test noise',[('IN','clk, rst, in_valid'),('IN','ecg [11:0]'),('IN','noise [11:0]'),('IN','k [2:0]    (= sw)'),('OUT','out_valid'),('OUT','y [DW-1:0]')])
mod(X[2],Y1,'baseline_remove','removes slow drift',[('IN','clk, rst, in_valid'),('IN','x [DW-1:0]'),('OUT','out_valid'),('OUT','y [DW-1:0]')])
mod(X[3],Y1,'fir_bp','band-pass 5 to 20 Hz',[('IN','clk, rst, in_valid'),('IN','x [DW-1:0]'),('OUT','out_valid'),('OUT','y [DW-1:0]'),('','SEQ=1: one multiplier')])
mod(X[4],Y1,'derivative','5-point slope',[('IN','clk, rst, in_valid'),('IN','x [DW-1:0]'),('OUT','out_valid'),('OUT','d [DW-1:0]')])
mod(X[4],Y2,'squarer','d x d, shifted by SQSH',[('IN','clk, rst, in_valid'),('IN','d [DW-1:0]'),('OUT','out_valid'),('OUT','sq [SQW-1:0]')])
mod(X[3],Y2,'mwi','150 ms running sum',[('IN','clk, rst, in_valid'),('IN','sq [SQW-1:0]'),('OUT','out_valid'),('OUT','env [EW-1:0]')])
mod(X[2],Y2,'qrs_decision','threshold, 200 ms, search-back',[('IN','clk, rst, in_valid'),('IN','env [EW-1:0]'),('OUT','det_valid'),('OUT','det_p [31:0]'),('OUT','thr_out [EW-1:0]')])
mod(X[1],Y2,'rpeak_locator','finds the exact R-peak',[('IN','clk, rst'),('IN','hp_valid'),('IN','hp [DW-1:0]'),('IN','det_valid'),('IN','det_p [31:0]'),('OUT','out_valid'),('OUT','rpeak_idx [31:0]')])
mod(X[0],Y2,'rr_bpm','RR gap and heart rate',[('IN','clk, rst'),('IN','r_valid'),('IN','r_idx [31:0]'),('OUT','rr [15:0]'),('OUT','bpm [15:0]'),('OUT','bpm_valid'),('','uses seq_div (divider)')],True)
# arrows row 1
for i in range(4): arrow((X[i]+233,341),(X[i+1],341)); dot(X[i]+233+16.5,341,i+1)
# 5 down
arrow((1522,525),(1522,614)); dot(1551,569,5)
# row 2 leftward
for i,n in zip([4,3,2,1],[6,7,8,9]): arrow((X[i],757),(X[i-1]+233,757)); dot(X[i]-16.5,757,n)
# 11 dashed
line([990,990,723],[525,566,566],GRY,'--',2); arrow((723,566),(723,614),GRY,'--',2); dot(960,544,11,GRY)
# 10 to outputs
line([456,456],[941,952]); line([456,1660],[952,952]); arrow((1660,952),(1690,952)); arrow((456,952),(456,941)); dot(489,923,10)
# output ports
box(1690,131,1977,983,'#E8F2E3','#2F7D32')
T(1833,155,'OUTPUT PORTS',14,'#2F7D32','bold','center'); T(1833,187,'(the main results only)',10.3,'#555','normal','center','italic')
outs=[('done','recording fully processed'),('rpeak_valid','1 pulse per heartbeat'),('rpeak_idx [31:0]','sample number of the R-peak'),('rr_samples [15:0]','samples between two beats'),('bpm [15:0]','heart rate in beats per minute'),('bpm_valid','bpm is ready to read')]
for i,(a,b) in enumerate(outs):
    y=250+i*98; T(1710,y,a,12.5,NAVY,'bold'); T(1710,y+30,b,10.3,'#333')
T(1710,860,'Heart-rate and beat count come from',9.8,'#555','normal','left','italic'); T(1710,880,'these ports. The board shows bpm on',9.8,'#555','normal','left','italic'); T(1710,900,'HEX2..HEX0 and beats on LEDR9.',9.8,'#555','normal','left','italic')
# bottom left table
box(23,1001,985,1395,'white','#9CA3AF',2)
T(42,1021,'Numbered signals between modules (inside the chip, not ports)',13,NAVY,'bold')
nums=[('valid, ecg, noise','sample_source to noise_injector'),('x_v, x [DW-1:0]','noise_injector to baseline_remove'),('hp_v, hp [DW-1:0]','baseline_remove to fir_bp'),('bp_v, bp [DW-1:0]','fir_bp to derivative'),('d_v, d [DW-1:0]','derivative to squarer'),('sq_v, sq [SQW-1:0]','squarer to mwi'),('env_v, env [EW-1:0]','mwi to qrs_decision'),('det_v, det_p [31:0]','qrs_decision to rpeak_locator'),('rpeak_valid, rpeak_idx','rpeak_locator to rr_bpm'),('rr, bpm, bpm_valid','rr_bpm to the output ports'),('hp_v, hp (dashed)','baseline_remove to rpeak_locator: stored ECG for the R-peak search')]
for i,(a,b) in enumerate(nums):
    y=1055+i*32; dot(52,y,i+1,ORG if i<10 else GRY); T(82,y,a,11.5,'#111','bold'); T(358,y,b,11)
# bottom right: ports in GTKWave order
box(998,1001,1977,1395,'white','#9CA3AF',2)
T(1017,1021,'Top-level ports in GTKWave order: inputs first, then outputs',13,NAVY,'bold')
T(1017,1060,'INPUT PORTS',11.5,ORG,'bold')
hdr=lambda y:(T(1017,y,'GTKWave name',9.6,'#666','bold'),T(1250,y,'port',9.6,'#666','bold'),T(1480,y,'meaning',9.6,'#666','bold'))
inp=[('clk','clk  (input)','50 MHz clock'),('rst','rst  (input)','reset'),('sw','sw [2:0]  (input)','noise level, 0 = clean ... 7 = very noisy')]
for i,(a,b,c) in enumerate(inp):
    y=1090+i*27; T(1017,y,a,11.2,BLUE,'bold'); T(1250,y,b,10.8); T(1480,y,c,10.3,'#555')
T(1017,1186,'OUTPUT PORTS',11.5,'#2F7D32','bold')
out=[('done','done','recording finished'),('beat_pulse','rpeak_valid','one pulse per heartbeat'),('rpeak_index','rpeak_idx [31:0]','exact R-peak sample'),('rr_samples','rr_samples [15:0]','samples between beats'),('bpm_valid','bpm_valid','new heart rate ready'),('bpm','bpm [15:0]','heart rate in BPM')]
for i,(a,b,c) in enumerate(out):
    y=1214+i*27; T(1017,y,a,11.2,BLUE,'bold'); T(1250,y,b,10.8); T(1480,y,c,10.3,'#555')
T(1017,1380,'GTKWave shows numbers in hex by default: right-click a signal, Data Format, Decimal.  Internal stage signals are shown only in the zoom pictures.',9.2,'#555','normal','left','italic')
fig.savefig('/mnt/user-data/outputs/ECG_QRS_Top_Level_Ports_Diagram.png',dpi=165)
fig.savefig('/mnt/user-data/outputs/ECG_QRS_Top_Level_Ports_Diagram.pdf')
print('ok')
