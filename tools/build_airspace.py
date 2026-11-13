#!/usr/bin/env python3
"""EASYFLY - extrait les espaces aériens utiles au vol ULM (CTR, TMA, CTA basses, P, R, D, RMZ, TMZ)
depuis france.geojson du dépôt planeur-net/airspace (FFVP, d'après l'AIP du SIA).
Usage : build_airspace.py <france.geojson> <sortie airspace.json> [date du commit source]"""
import json, sys, datetime

KEEP = {'CTR', 'TMA', 'CTA', 'P', 'R', 'Q', 'RMZ', 'TMZ'}
MAX_FLOOR_FT = 11500          # au-dessus : sans intérêt pour un ULM

def ft(c):
    if not c: return None
    v, u, r = c.get('value'), c.get('unit'), c.get('referenceDatum')
    if v is None: return None
    if u == 'FL': return v * 100
    if u == 'M': return round(v * 3.28084)
    return v                   # FT (MSL ou GND)

def lim(c):
    if not c: return None
    return [c.get('value'), c.get('unit'), c.get('referenceDatum')]

def main(src, dst, srcdate=''):
    F = json.load(open(src, encoding='utf-8'))['features']
    out = []
    for f in F:
        p = f['properties']; t = p.get('type')
        if t not in KEEP: continue
        lo = ft(p.get('lowerCeiling'))
        if lo is not None and p.get('lowerCeiling', {}).get('referenceDatum') != 'GND' and lo >= MAX_FLOOR_FT: continue
        g = f['geometry']
        if g['type'] != 'Polygon': continue
        ring = [[round(y, 4), round(x, 4)] for x, y in g['coordinates'][0]]
        # supprime les points consécutifs identiques après arrondi
        r2 = [ring[0]]
        for q in ring[1:]:
            if q != r2[-1]: r2.append(q)
        if len(r2) < 4: continue
        la = [q[0] for q in r2]; lo_ = [q[1] for q in r2]
        sp = {'n': p.get('name'), 't': t, 'c': p.get('class'), 'lo': lim(p.get('lowerCeiling')), 'up': lim(p.get('upperCeiling')),
              'bb': [min(la), min(lo_), max(la), max(lo_)], 'ring': r2}
        fr = p.get('frequency')
        if fr and fr.get('value'):
            sp['f'] = fr['value']; sp['fn'] = fr.get('name')
        out.append(sp)
    doc = {'source': 'planeur-net/airspace (FFVP, d\'après l\'AIP du SIA)' + (' — ' + srcdate if srcdate else ''),
           'generated': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), 'count': len(out), 'spaces': out}
    json.dump(doc, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(len(out), 'espaces ->', dst)

if __name__ == '__main__':
    main(*sys.argv[1:4])
