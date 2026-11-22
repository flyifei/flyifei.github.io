"""Extract departure/arrival legs from an MSFS 2024 logbook (sr_logbook, Steam cloud).

The file is a proprietary binary stream: length-prefixed strings mixed with binary
fields. Airport ICAO codes appear as b'\x04ABCD'. Consecutive duplicates are
collapsed, then neighbouring airports are counted as legs.

Usage:  python extract_routes.py <sr_logbook> > routes.csv
"""
import sys, re, collections, csv

path = sys.argv[1]
data = open(path, 'rb').read()

icao = re.compile(rb'\x04([A-Z][A-Z0-9]{3})')
tokens = [m.group(1).decode() for m in icao.finditer(data)]

# collapse runs (each airport is written several times per record)
seq = []
for t in tokens:
    if not seq or seq[-1] != t:
        seq.append(t)

legs = collections.Counter(zip(seq, seq[1:]))
w = csv.writer(sys.stdout, lineterminator='\n')
w.writerow(['from', 'to', 'count'])
for (a, b), n in legs.most_common():
    w.writerow([a, b, n])