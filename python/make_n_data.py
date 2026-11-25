# cut the first N samples of the ROM files:  python make_n_data.py N
import sys
n=int(sys.argv[1]) if len(sys.argv)>1 else 7200
for f in ('ecg','noise'):
    L=open('sim/%s.hex'%f).read().split('\n')[:n]; open('sim/%s_n.hex'%f,'w').write('\n'.join(L)+'\n')
print('ROM files cut to %d samples'%n)
