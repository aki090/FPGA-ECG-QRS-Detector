# cut the first 10 s (3600 samples) of the ROM files for the short demo simulation
for n in ('ecg','noise'):
    L=open('sim/%s.hex'%n).read().split('\n')[:3600]; open('sim/%s_demo.hex'%n,'w').write('\n'.join(L)+'\n')
print('demo data ready (3600 samples)')
