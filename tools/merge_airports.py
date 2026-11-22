import csv, json, sys

oa_csv, base_json, out_json = sys.argv[1], sys.argv[2], sys.argv[3]
want = set('AZ22 FMAD LEPF NZQE WACX WT86 WX53'.split())

found = {}
with open(oa_csv, encoding='utf-8', newline='') as f:
    for row in csv.DictReader(f):
        for key in ('ident', 'icao_code', 'gps_code', 'local_code'):
            v = (row.get(key) or '').strip().upper()
            if v in want and v not in found:
                try:
                    lat = float(row['latitude_deg']); lon = float(row['longitude_deg'])
                except Exception:
                    continue
                found[v] = {'icao': v, 'name': row.get('name') or v, 'city': row.get('municipality') or '',
                            'country': row.get('iso_country') or '', 'lat': lat, 'lon': lon}

data = json.load(open(base_json, encoding='utf-8'))
for k, v in found.items():
    data.setdefault(k, v)
json.dump(data, open(out_json, 'w', encoding='utf-8'), ensure_ascii=False)
print('resolved:', ', '.join('%s (%s)' % (k, v['name']) for k, v in found.items()) or 'none')
print('still missing:', ', '.join(sorted(want - set(found))) or 'none')
print('base entries:', len(data))