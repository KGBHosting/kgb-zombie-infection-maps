#!/usr/bin/env python3
"""Bounded BSP30 inspection plus real compiled standing-hull navigation sampling.
This does not emulate GoldSrc movement or certify client/gameplay acceptance.
"""
import argparse
from collections import Counter, deque
import hashlib
import json
import math
from pathlib import Path
import re
import struct

EMPTY, SOLID = -1, -2
CLASSES = {'worldspawn','info_player_start','info_player_deathmatch','light'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


class BSP:
    def __init__(self, data):
        self.data=data
        require(len(data)>=124 and struct.unpack_from('<i',data)[0]==30,'GoldSrc BSP30 required')
        self.lumps=[struct.unpack_from('<ii',data,4+8*i) for i in range(15)]
        for o,n in self.lumps:
            require(0<=o<=len(data) and 0<=n<=len(data)-o,'lump bounds invalid')
        require(b'BSPX' not in data[max(o+n for o,n in self.lumps):],'BSPX extensions not accepted')
        self.planes=list(struct.iter_unpack('<4fi',self.lump(1)))
        self.clips=list(struct.iter_unpack('<ihh',self.lump(9)))
        self.models=list(struct.iter_unpack('<9f7i',self.lump(14)))
        require(len(self.models)==1,'unexpected model/brush entity')
        for p,a,b in self.clips:
            require(0<=p<len(self.planes) and all(c<0 or c<len(self.clips) for c in (a,b)),'bad clipnode index')
        raw=self.lump(0).decode('ascii').strip('\0\n ')
        self.entities=[dict(re.findall(r'"([^"\n]*)"\s*"([^"\n]*)"',s)) for s in re.findall(r'\{(.*?)\}',raw,re.S)]

    def lump(self,i):
        o,n=self.lumps[i]
        return self.data[o:o+n]

    def contents(self,p,hull=1):
        n=self.models[0][9+hull]
        count=0
        while n>=0:
            count+=1
            require(count<=len(self.clips)+1,'clipnode cycle')
            pi,a,b=self.clips[n]
            nx,ny,nz,d,_=self.planes[pi]
            n=a if p[0]*nx+p[1]*ny+p[2]*nz>=d else b
        return n

    def embedded_textures(self):
        tex=self.lump(2)
        count=struct.unpack_from('<i',tex)[0]
        require(0<count<512,'unexpected texture count')
        names=[]
        for i in range(count):
            o=struct.unpack_from('<i',tex,4+4*i)[0]
            require(o>=4+4*count and o+40<=len(tex),'missing texture')
            name,w,h,*mips=struct.unpack_from('<16s6i',tex,o)
            name=name.split(b'\0')[0].decode('ascii')
            require(name.startswith('zi_') or name=='skip','texture not first-party allowlist')
            require(w==128 and h==128,'unexpected texture dimensions')
            for level,off in enumerate(mips):
                require(off>=40 and o+off+(w>>level)*(h>>level)<=len(tex),'external or truncated miptexture')
            end=o+mips[-1]+(w>>3)*(h>>3)
            require(end+770<=len(tex) and struct.unpack_from('<H',tex,end)[0]==256,'WAD3 palette missing')
            names.append(name)
        return names

    def floor_levels(self):
        levels={0}
        for face in struct.iter_unpack('<HHiHH4Bi',self.lump(7)):
            pi,side=face[:2]
            nx,ny,nz,d,_=self.planes[pi]
            if nx==0 and ny==0 and nz*(1 if side==0 else -1)>0.9:
                z=d/nz
                if 0<=z<=224:
                    levels.add(round(z,3))
        return sorted(levels)


def inspect(path, navigation=True):
    data=path.read_bytes(); b=BSP(data)
    counts=Counter(e.get('classname') for e in b.entities)
    require(set(counts)<=CLASSES,'unexpected entity class/objective or asset dependency')
    require(counts['worldspawn']==1 and counts['info_player_start']==32 and counts['info_player_deathmatch']==32,'exact32CT+32T required')
    require(b.lumps[8][1]>0 and b.lumps[8][1]%3==0,'RGB lighting missing')
    require(b.lumps[4][1]>0,'VIS missing')
    textures=b.embedded_textures()
    for e in b.entities:
        require(not any(k in e for k in ('model','noise','sound','skyname','sky')),'external client asset reference')
    spawns=[tuple(map(float,e['origin'].split())) for e in b.entities if e.get('classname') in ('info_player_start','info_player_deathmatch')]
    require(len(set(spawns))==64,'spawn origins overlap')
    for i,p in enumerate(spawns):
        require(b.contents(p,1)==EMPTY and b.contents(p,3)==EMPTY,'spawn blocked in compiled player hull')
        require(b.contents((p[0],p[1],35),1)==SOLID,'spawn lacks floor support')
        for q in spawns[i+1:]:
            require(abs(p[0]-q[0])>=32 or abs(p[1]-q[1])>=32 or abs(p[2]-q[2])>=72,'player spawn hulls overlap')
    result={'map':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'sha512':hashlib.sha512(data).hexdigest(),
            'bsp_version':30,'ct_spawns':32,'t_spawns':32,'all_spawn_hulls_clear':True,'spawn_hulls_nonoverlapping':True,
            'embedded_textures':textures,'external_client_assets':[],'light_bytes':b.lumps[8][1],'vis_bytes':b.lumps[4][1],
            'faces':len(b.lump(7))//20,'clipnodes':len(b.clips),'entity_classes':dict(counts)}
    if navigation:
        result['navigation']=navigation_check(b,path.stem,spawns)
    return result


def navigation_check(b,name,spawns):
    # 32-unit horizontal grid, all actual upward-facing compiled floor heights <=224.
    levels=b.floor_levels()
    nodes=set()
    for x in range(-1232,1233,32):
        for y in range(-1232,1233,32):
            for z in levels:
                if b.contents((x,y,z+36.125))==EMPTY and b.contents((x,y,z+35.875))==SOLID:
                    nodes.add((x,y,z))
    def clear_step(a,c):
        if abs(c[2]-a[2])>18:
            return False
        z=max(a[2],c[2])+36.125
        return all(b.contents((a[0]+(c[0]-a[0])*i/4,a[1]+(c[1]-a[1])*i/4,z))==EMPTY for i in range(5))
    byxy={}
    for n in nodes:
        byxy.setdefault(n[:2],[]).append(n)
    def nearest(p,z):
        options=[n for n in nodes if abs(n[0]-p[0])<=24 and abs(n[1]-p[1])<=24 and abs(n[2]-z)<0.1]
        require(options,'no sampled standing-floor node near target')
        return min(options,key=lambda n:math.dist(n[:2],p[:2]))
    first=nearest(spawns[0],0); seen={first}; q=deque([first])
    while q:
        a=q.popleft()
        for dx,dy in ((32,0),(-32,0),(0,32),(0,-32)):
            for c in byxy.get((a[0]+dx,a[1]+dy),()):
                if c not in seen and clear_step(a,c):
                    seen.add(c);q.append(c)
    require(all(nearest(p,0) in seen for p in spawns),'spawn regions disconnected')
    if 'courtyard' in name:
        targets=[('fort south',(-144,-224),128),('fort north',(144,224),128)]
        targets +=[(f'arcade{x} {y}',(x,y),64) for x in (-816,816) for y in (-240,240)]
    elif 'depot' in name:
        targets=[(f'loading{x} {y}',(x,y),160) for x in (-800,800) for y in (-320,320)]
        targets += [('catwalk west',(-512,0),160),('catwalk east',(512,0),160)]
    else:
        targets=[('control south',(0,-96),64),('control north',(0,96),64)]
        targets += [(f'room{x} {y} side{side}',(x+side*80,y),64) for x in (-720,720) for y in (-352,352) for side in (-1,1)]
    require(all(nearest(p,z) in seen for _,p,z in targets),'declared defense approach not reachable on standing-hull grid')
    return {'method':'compiled GoldSrc hull1;32-unit XY grid,18-unit maximum step,4 subsegments per move; no jump simulation',
            'sampled_nodes':len(nodes),'reachable_nodes':len(seen),'spawn_regions_connected':True,
            'defense_approach_targets_reached':[label for label,_,_ in targets],
            'limits':'Sampling cannot prove continuous engine movement, collision-free simultaneous spawning, balance or client behavior.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',nargs='?',default='build/candidate');parser.add_argument('--no-navigation',action='store_true')
    args=parser.parse_args()
    paths=sorted(Path(args.directory).glob('*.bsp'));require(len(paths)==3,'three BSP files required')
    results=[inspect(p,not args.no_navigation) for p in paths]
    print(json.dumps({'maps':results,'live_tested':False},indent=2))
