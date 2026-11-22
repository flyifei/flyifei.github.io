import sys, re, json

path = sys.argv[1]
data = open(path, 'rb').read()

# 每条记录都包含一次 creator 字符串；用它切分记录
creator = b'\x0cAsobo Studio'
idx = [m.start() for m in re.finditer(re.escape(creator), data)]
print('records (creator markers):', len(idx))

icao_re = re.compile(rb'\x04([A-Z][A-Z0-9]{3})')

def strings_between(a, b):
    out = []
    i = a
    while i < b:
        L = data[i]
        if 3 <= L <= 60 and i + 1 + L <= b:
            seg = data[i+1:i+1+L]
            if all(32 <= x < 127 for x in seg):
                out.append((i, seg.decode('ascii')))
                i += 1 + L
                continue
        i += 1
    return out

starts = [0] + [i - 40 for i in idx]  # 粗略记录起点
recs = []
for n, c in enumerate(idx):
    a = 0 if n == 0 else idx[n-1]
    seg = data[a:c]
    toks = [m.group(1).decode() for m in icao_re.finditer(seg)]
    strs = strings_between(a, c)
    # 机型标题：creator 之后紧跟的 id 与标题
    after = strings_between(c, idx[n+1] if n+1 < len(idx) else len(data))
    ac_id = next((s for _, s in after if s.startswith(('asobo-', 'microsoft-', 'inibuilds-'))), '')
    ac_title = next((s for _, s in after if not s.startswith(('asobo-', 'microsoft-', 'inibuilds-')) and len(s) > 8 and s not in ('PLANETYPE_PROPELLER','PLANETYPE_JET')), '')
    if not toks:
        continue
    recs.append({'idx': n, 'dep': toks[0], 'arr': toks[-1], 'ntok': len(toks), 'ac_id': ac_id, 'ac': ac_title})

print('records with tokens:', len(recs))
for r in recs[:40]:
    print('%3d  %-4s -> %-4s  tok=%-2d  %-34s %s' % (r['idx'], r['dep'], r['arr'], r['ntok'], r['ac_id'][:34], r['ac']))