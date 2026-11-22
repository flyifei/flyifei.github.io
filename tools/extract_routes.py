"""Extract legs, with aircraft type, from an MSFS 2024 logbook (sr_logbook).

Reverse-engineered layout of one entry in the binary stream:

    [ airport codes ... ][ b'\x0cAsobo Studio' ][ planet type ][ aircraft id ][ title ]

so an entry's airport codes come *before* its aircraft id. Entries are delimited
by the creator marker. Within an entry each airport code is repeated once per
stored field, so runs are collapsed; the remainder alternates departure and
arrival. An entry with a single airport is a local circuit (from == to).

An airport is attributed to the first aircraft id at or after its offset.

Usage:  python extract_routes.py <sr_logbook> > routes.csv
Output: from,to,aircraft,count
"""
import sys, re, collections, csv, bisect

AC_NAMES = [
    ('c172sp', 'C172S'), ('c152', 'C152'), ('da40', 'DA40'), ('da62', 'DA62'),
    ('dhc6', 'DHC-6'), ('208b', 'C208B'), ('savage-cub', 'Savage Cub'),
    ('b737max', '737 MAX'), ('a350', 'A350'), ('c400', 'C400'), ('sf50', 'SF50'),
    ('vl3', 'VL-3'), ('fa18', 'F/A-18E'), ('optica', 'Optica'),
    ('a320', 'A320'), ('a321', 'A321'), ('a330', 'A330'), ('b747', '747'),
    ('b787', '787'), ('atr', 'ATR'), ('crj', 'CRJ'), ('e170', 'E170'),
]


def label(ac_id):
    s = ac_id.lower()
    for key, name in AC_NAMES:
        if key in s:
            return name
    return ac_id.split('aircraft-')[-1][:14]


def main(path):
    data = open(path, 'rb').read()
    icao = re.compile(rb'\x04([A-Z][A-Z0-9]{3})')
    acid = re.compile(rb'((?:asobo|microsoft|inibuilds)-aircraft-[a-z0-9\-]{3,40})')
    marks = [m.start() for m in re.finditer(re.escape(b'\x0cAsobo Studio'), data)]

    planes = []
    for m in acid.finditer(data):
        name = label(m.group(1).decode())
        if not planes or planes[-1][1] != name:
            planes.append((m.start(), name))
    offsets = [p[0] for p in planes]

    def ac_for(off):
        i = bisect.bisect_left(offsets, off)
        if i < len(planes):
            return planes[i][1]
        return planes[-1][1] if planes else 'unknown'

    legs = collections.Counter()
    for n, mark in enumerate(marks):
        start = 0 if n == 0 else marks[n - 1]
        toks = []
        for m in icao.finditer(data, start, mark):
            code = m.group(1).decode()
            if not toks or toks[-1][1] != code:
                toks.append((m.start(), code))
        if not toks:
            continue
        if len(toks) == 1:
            off, code = toks[0]
            legs[(code, code, ac_for(off))] += 1
            continue
        for (o1, c1), (o2, c2) in zip(toks, toks[1:]):
            if c1 != c2:
                legs[(c1, c2, ac_for(o1))] += 1

    w = csv.writer(sys.stdout, lineterminator='\n')
    w.writerow(['from', 'to', 'aircraft', 'count'])
    for (a, b, ac), n in sorted(legs.items(), key=lambda kv: (-kv[1], kv[0])):
        w.writerow([a, b, ac, n])


if __name__ == '__main__':
    main(sys.argv[1])