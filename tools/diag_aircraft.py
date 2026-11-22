import sys, re
data = open(sys.argv[1], 'rb').read()
marks = [m.start() for m in re.finditer(re.escape(b'\x0cAsobo Studio'), data)]
icao = re.compile(rb'\x04([A-Z][A-Z0-9]{3})')
acid = re.compile(rb'((?:asobo|microsoft|inibuilds)-aircraft-[a-z0-9\-]{3,40})')
for n, mark in enumerate(marks):
    start = 0 if n == 0 else marks[n-1]
    nxt = marks[n+1] if n+1 < len(marks) else len(data)
    seg = data[start:mark]; after = data[mark:nxt]
    acs = [a.decode() for a in acid.findall(after)]
    seq = []
    for m in icao.finditer(seg):
        c = m.group(1).decode()
        if not seq or seq[-1] != c: seq.append(c)
    blob = ' '.join(acs)
    if ('a350' in blob or 'dhc6' in blob or 'c400' in blob or 'sf50' in blob or 'optica' in blob) or not acs:
        print('%3d  acs=%s  seg=%d  seq=%s' % (n, acs or 'NONE', len(seg), ' > '.join(seq) if seq else '(none)'))