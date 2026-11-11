#!/usr/bin/env python3
"""Original CC0 brush layouts and procedural textures. No game/customer assets."""
import hashlib
import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('zm_kgb_courtyard_v1', 'zm_kgb_depot_v1', 'zm_kgb_containment_v1')


def rgb_texture(kind, x, y):
    n = ((x * 13 + y * 29 + (x * y) % 17) % 9) - 4
    if kind == 'zi_brick':
        joint = y % 32 < 3 or (x + (32 if y // 32 % 2 else 0)) % 64 < 3
        c = (62, 55, 48) if joint else (135 + n, 109 + n, 84 + n)
    elif kind == 'zi_floor':
        c = (38, 45, 49) if x % 64 < 3 or y % 64 < 3 else (83+n, 91+n, 94+n)
    elif kind == 'zi_metal':
        seam = x % 64 < 3 or y % 64 < 3
        rivet = (x % 64 - 8)**2 + (y % 64 - 8)**2 < 5
        c = (27, 40, 48) if seam else (153, 164, 169) if rivet else (63+n, 86+n, 103+n)
    elif kind == 'zi_crate':
        frame = x < 10 or x > 117 or y < 10 or y > 117 or abs(x-y) < 5
        c = (71, 51, 32) if frame else (141+n, 107+n, 67+n)
    elif kind == 'zi_caution':
        c = (213, 169, 40) if (x+y) % 48 < 24 else (31, 36, 38)
    elif kind == 'zi_lab':
        c = (27, 94, 84) if 46 <= y % 64 <= 54 else (94, 106, 107) if x % 64 < 2 or y % 64 < 2 else (174+n, 185+n, 181+n)
    elif kind == 'zi_green':
        c = (18, 49, 42) if x % 32 < 3 or y % 64 < 3 else (57+n, 116+n, 89+n)
    elif kind == 'zi_ceiling':
        c = (47, 65, 72) if x % 64 < 2 or y % 64 < 2 else (123+n, 152+n, 159+n)
    elif kind == 'zi_light':
        c = (42, 50, 53) if x < 8 or x > 119 or y < 8 or y > 119 else (213, 225, 210)
    elif kind == 'zi_trim':
        c = (45, 52, 54) if x % 32 < 3 else (102+n, 113+n, 118+n)
    else:
        c = (107+n, 111+n, 106+n)
    return tuple(max(0, min(255, a)) for a in c)


def write_wad():
    names = ('zi_brick', 'zi_floor', 'zi_metal', 'zi_crate', 'zi_caution', 'zi_lab',
             'zi_green', 'zi_ceiling', 'zi_light', 'zi_trim', 'zi_concrete', 'skip')
    data = bytearray(b'WAD3' + struct.pack('<ii', len(names), 0))
    entries = []
    for name in names:
        pixels = [rgb_texture(name, x, y) for y in range(128) for x in range(128)]
        palette = sorted(set(pixels))
        assert len(palette) <= 256, (name, len(palette))
        lookup = {c: i for i, c in enumerate(palette)}
        levels = []
        for scale in (1, 2, 4, 8):
            levels.append(bytes(lookup[pixels[y*128+x]] for y in range(0,128,scale) for x in range(0,128,scale)))
        off, offsets = 40, []
        for level in levels:
            offsets.append(off)
            off += len(level)
        lump = (name.encode().ljust(16,b'\0') + struct.pack('<6i',128,128,*offsets) + b''.join(levels)
                + struct.pack('<H',256) + b''.join(bytes(c) for c in palette) + bytes((256-len(palette))*3))
        entries.append((len(data),len(lump),name))
        data.extend(lump)
    directory = len(data)
    for offset, length, name in entries:
        data.extend(struct.pack('<iiiBBH16s',offset,length,length,0x43,0,0,name.encode().ljust(16,b'\0')))
    struct.pack_into('<i',data,8,directory)
    path = ROOT/'assets/kgb_original.wad'
    path.write_bytes(data)
    return {'path':str(path.relative_to(ROOT)), 'sha256':hashlib.sha256(data).hexdigest(), 'textures':list(names)}


class Map:
    def __init__(self, name, theme, wall):
        self.name, self.theme = name, theme
        self.brushes, self.entities, self.design = [], [], []
        self.box((-1312,-1312,-32),(1312,1312,0),'zi_floor','floor')
        self.box((-1312,-1312,512),(1312,1312,544),'zi_ceiling','ceiling')
        self.box((-1312,-1312,0),(-1280,1312,512),wall,'west enclosure')
        self.box((1280,-1312,0),(1312,1312,512),wall,'east enclosure')
        self.box((-1280,-1312,0),(1280,-1280,512),wall,'south enclosure')
        self.box((-1280,1280,0),(1280,1312,512),wall,'north enclosure')
        # All humans begin CT: 32 unobstructed CT origins, not merely 16+16 total.
        for team, sign, angle in (('info_player_start',1,270),('info_player_deathmatch',-1,90)):
            for row in range(4):
                for col in range(8):
                    self.ent(team, ((col-3.5)*96, sign*(832+row*96), 40), angle=str(angle))
        for x in (-960,-480,0,480,960):
            for y in (-960,-480,0,480,960):
                self.ent('light',(x,y,416),light='650',_color='1 0.95 0.86')
        # Recessed decorative light panels are ordinary original-textured world brushes.
        for x in (-960,-480,0,480,960):
            for y in (-960,0,960):
                self.box((x-48,y-48,504),(x+48,y+48,512),'zi_light','ceiling fixture')

    def box(self, lo, hi, texture, label='structure'):
        assert all(lo[i]<hi[i] for i in range(3)), (lo,hi)
        self.brushes.append((tuple(lo),tuple(hi),texture,label))

    def ent(self, classname, origin, **kv):
        self.entities.append({'classname':classname,'origin':' '.join(f'{v:g}' for v in origin),**kv})

    def stairs(self, x0, x1, y_edge, direction, height, label):
        """16-high,32-deep ordinary stairs; direction points from platform to ground."""
        assert height % 16 == 0
        for step in range(height//16):
            a,b=y_edge+direction*step*32,y_edge+direction*(step+1)*32
            self.box((x0,min(a,b),0),(x1,max(a,b),height-step*16),'zi_trim',label)

    def stairs_x(self, y0, y1, x_edge, direction, height, label):
        for step in range(height//16):
            a,b=x_edge+direction*step*32,x_edge+direction*(step+1)*32
            self.box((min(a,b),y0,0),(max(a,b),y1,height-step*16),'zi_trim',label)

    def crate(self,x,y, size=128):
        self.box((x-size/2,y-size/2,0),(x+size/2,y+size/2,96),'zi_crate','sightline cover')
        # Both sides offer ordinary 48-unit steps, so the roof has two approaches.
        self.box((x-size/2-48,y-48,0),(x-size/2,y+48,48),'zi_crate','west crate step')
        self.box((x+size/2,y-48,0),(x+size/2+48,y+48,48),'zi_crate','east crate step')

    def write(self):
        out=['// Original CC0 map; generated by tools/generate.py. No external game artwork.', '{',
             '"classname" "worldspawn"', '"mapversion" "220"',
             '"wad" "kgb_original.wad"', f'"message" "KGB {self.theme}"', '"_minlight" "12"']
        for lo,hi,tex,label in self.brushes:
            x,y,z=lo; X,Y,Z=hi
            faces=(((x,y,z),(x,y,Z),(x,Y,Z)), ((X,y,z),(X,Y,z),(X,Y,Z)),
                   ((x,y,z),(X,y,z),(X,y,Z)), ((x,Y,z),(x,Y,Z),(X,Y,Z)),
                   ((x,y,z),(x,Y,z),(X,Y,z)), ((x,y,Z),(X,y,Z),(X,Y,Z)))
            out.append('{ // '+label)
            for face in faces:
                face=(face[0],face[2],face[1])  # .map plane winding is clockwise from outside.
                points=' '.join('( '+' '.join(f'{a:g}' for a in p)+' )' for p in face)
                out.append(f'{points} {tex} 0 0 0 1 1')
            out.append('}')
        out.append('}')
        for ent in self.entities:
            out.extend(['{',*['"'+k+'" "'+v+'"' for k,v in ent.items()],'}'])
        (ROOT/'src'/f'{self.name}.map').write_text('\n'.join(out)+'\n')
        (ROOT/'src'/f'{self.name}.geometry.json').write_text(json.dumps({
            'name':self.name, 'theme':self.theme, 'brushes':[
                {'mins':a,'maxs':b,'texture':t,'label':l} for a,b,t,l in self.brushes],
            'entities':self.entities, 'defense_positions':self.design},indent=2)+'\n')


def courtyard():
    m=Map(NAMES[0],'Courtyard Fort','zi_brick')
    m.box((-288,-288,0),(288,288,128),'zi_brick','central fort')
    m.stairs(-224,-64,-288,-1,128,'south fort approach')
    m.stairs(64,224,288,1,128,'north fort approach')
    # Broken parapets preserve cover without creating an enclosed unreachable nest.
    for x in (-288,224):
        for y in (-288,192):
            m.box((x,y,128),(x+64,y+96,192),'zi_brick','fort parapet')
    for y in (-288,256):
        m.box((-32,y,128),(128,y+32,176),'zi_caution','fort low shield')
    m.box((-48,-48,128),(48,48,256),'zi_trim','fort core pillar')
    # Twin arcade positions: open at both ends, wide flank alleys behind them.
    for sign in (-1,1):
        x=sign*816
        m.box((x-144,-320,0),(x+144,320,64),'zi_concrete','arcade dais')
        m.stairs(x-96,x+96,-320,-1,64,'south arcade approach')
        m.stairs(x-96,x+96,320,1,64,'north arcade approach')
        for y in (-288,256):
            m.box((x-144,y,64),(x-96,y+32,256),'zi_brick','arcade pillar')
            m.box((x+96,y,64),(x+144,y+32,256),'zi_brick','arcade pillar')
        m.box((x-144,-320,256),(x+144,320,288),'zi_brick','arcade canopy')
        m.box((x-64,-96,64),(x+64,-64,112),'zi_brick','arcade shield')
    for x in (-480,480):
        for y in (-528,528):
            m.crate(x,y,96)
    m.design=[{'name':'central fort','floor_z':128,'approaches':['south stairs','north stairs']},
              {'name':'west arcade','floor_z':64,'approaches':['south stairs','north stairs']},
              {'name':'east arcade','floor_z':64,'approaches':['south stairs','north stairs']}]
    return m


def depot():
    m=Map(NAMES[1],'Industrial Depot','zi_metal')
    for x in (-800,800):
        m.box((x-160,-384,0),(x+160,384,160),'zi_metal','loading platform')
        m.stairs(x-80,x+80,-384,-1,160,'south loading stairs')
        m.stairs(x-80,x+80,384,1,160,'north loading stairs')
        for y in (-288,256):
            m.box((x-160,y,160),(x-112,y+32,216),'zi_caution','platform shield')
            m.box((x+112,y,160),(x+160,y+32,216),'zi_caution','platform shield')
        m.box((x-96,-64,160),(x+96,-32,208),'zi_crate','loading cover')
    m.box((-640,-80,144),(640,80,160),'zi_trim','cross-warehouse catwalk')
    for x in (-512,480):
        m.box((x,-80,0),(x+32,-48,144),'zi_metal','catwalk support')
        m.box((x,48,0),(x+32,80,144),'zi_metal','catwalk support')
    for y in (-80,64):
        for x in (-512,-128,256):
            m.box((x,y,160),(x+128,y+16,192),'zi_caution','broken catwalk rail')
    for x in (-384,384):
        for y in (-480,480):
            m.crate(x,y,160)
    for x in (-1152,1120):
        for y in (-640,0,640):
            m.box((x,y-32,0),(x+32,y+32,384),'zi_metal','warehouse column')
        m.box((x,-960,384),(x+32,960,416),'zi_trim','warehouse beam')
    m.design=[{'name':'west loading platform','floor_z':160,'approaches':['south loading stairs','north loading stairs','east catwalk']},
              {'name':'east loading platform','floor_z':160,'approaches':['south loading stairs','north loading stairs','west catwalk']},
              {'name':'catwalk','floor_z':160,'approaches':['west loading platform','east loading platform']}]
    return m


def containment():
    m=Map(NAMES[2],'Containment Facility','zi_lab')
    for sx in (-1,1):
        for sy in (-1,1):
            cx,cy=sx*720,sy*352
            # Two opposite 160-unit entrances per containment room.
            for yy in (cy-224,cy+192):
                m.box((cx-256,yy,0),(cx+256,yy+32,224),'zi_lab','containment room wall')
            for xx in (cx-256,cx+224):
                m.box((xx,cy-192,0),(xx+32,cy-80,224),'zi_lab','split room wall')
                m.box((xx,cy+80,0),(xx+32,cy+192,224),'zi_lab','split room wall')
            m.box((cx-112,cy-112,0),(cx+112,cy+112,64),'zi_green','containment dais')
            # Ordinary 16-unit stairs reach the dais through both doorways.
            m.stairs_x(cy-64,cy+64,cx-112,-1,64,'west dais approach')
            m.stairs_x(cy-64,cy+64,cx+112,1,64,'east dais approach')
            m.box((cx-48,cy-48,64),(cx+48,cy+48,160),'zi_green','containment pod cover')
            for yy in (cy-192,cy+160):
                m.box((cx-96,yy,0),(cx+96,yy+32,80),'zi_caution','room shield')
            m.ent('light',(cx,cy,192),light='280',_color='0.7 1 0.82')
    m.box((-128,-128,0),(128,128,64),'zi_trim','central control dais')
    m.stairs(-80,80,-128,-1,64,'south control stairs')
    m.stairs(-80,80,128,1,64,'north control stairs')
    m.box((-32,-32,64),(32,32,192),'zi_green','central control cover')
    m.design=[{'name':'central control','floor_z':64,'approaches':['south control stairs','north control stairs']},
              {'name':'four containment rooms','floor_z':64,'approaches':['west entrance + step','east entrance + step']}]
    return m


if __name__=='__main__':
    for folder in ('assets','src'):
        (ROOT/folder).mkdir(exist_ok=True)
    wad=write_wad()
    maps=[courtyard(),depot(),containment()]
    for m in maps:
        m.write()
    (ROOT/'assets/manifest.json').write_text(json.dumps({'license':'CC0-1.0','origin':'Original procedural pixels generated solely by tools/generate.py','wad':wad,'maps':list(NAMES)},indent=2)+'\n')
    print(json.dumps({'generated_maps':list(NAMES),'textures':len(wad['textures']),'third_party_art_assets':0}))
