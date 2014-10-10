from collections import defaultdict
import csv
import gzip
import networkx as nx

def load_gzip_csv(filename):
    """Helper function to load CSV data from a GZipped file"""
    gzfile = gzip.GzipFile(filename, 'rb')
    csvfile = csv.reader(gzfile)
    header_line = csvfile.next()
    print 'Reading from CSV file {fn} with headers {h}'.format(fn=filename, h=header_line)
    return csvfile

##################
# load and clean the data
#################
g = nx.DiGraph()
for pid, year in load_gzip_csv('rawdata/papers.csv.gz'):
    g.add_node(int(pid), year=int(year))
for p1, p2 in load_gzip_csv('rawdata/cites.csv.gz'):
    try:
        src = int(p1)
        dst = int(p2)
        # Filter out bad citations, which go backwards in year
        if g.node[src]['year'] >= g.node[dst]['year']:
            g.add_edge(src, dst)
    except KeyError:
        pass
print "Read {p} papers and {c} valid citations".format(p=g.number_of_nodes(), c=g.number_of_edges())

###################
# pick a set of seed papers
###################
N = 50
seeds = [p for p in g.nodes() if p <= N]
print "Chose {s} seed papers (have paper id <= {N})".format(s=len(seeds), N=N)

###################
# find all papers that any seed paper cites, plus the depth (# citation hops)
###################
citation_depths = {p: nx.single_source_shortest_path_length(g, p) for p in seeds}
print "{r} seed papers cite anything".format(r=len(citation_depths))

#####################
# helper to resolve the "least common ancestor"
#   The least common ancestor is the ancestor with smallest citation depth and
#   latest year. We break ties by picking the paper with the smallest paper ID.
#####################
def ancestor_key(x):
    a, d, y = x
    return (d, -y, a)

###################
# find the least common ancestor for every pair of papers
###################
lca = []
for p1, p2 in ((p1, p2) for p1 in seeds for p2 in seeds if p1 < p2):
    depths1 = citation_depths.get(p1, {})
    depths2 = citation_depths.get(p2, {})
    common = set(depths1).intersection(depths2)
    if not common:
        continue
    lca.append((p1, p2) + min(((a, max(depths1[a], depths2[a]), g.node[a]['year']) for a in common),
        key=ancestor_key))
print "{p} of the {allp} pairs of seed papers have a common ancestor".format(p=len(lca), allp=len(seeds)*(len(seeds)-1)/2)

with open('results.csv', 'wb') as resultsfile:
    writer = csv.writer(resultsfile)
    writer.writerow(['p1', 'p2', 'a', 'depth', 'year'])
    writer.writerows(sorted(lca))
print "Wrote {r} results to results.csv".format(r=len(lca))
