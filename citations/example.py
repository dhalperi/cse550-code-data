from collections import defaultdict
import csv
import gzip

def load_gzip_csv(filename):
    """Helper function to load CSV data from a GZipped file"""
    with gzip.GzipFile(filename, 'rb') as gzfile:
        csvfile = csv.reader(gzfile)
        header_line = csvfile.next()
        print 'Reading from CSV file {fn} with headers {h}'.format(fn=filename, h=header_line)
        return list(csvfile)

##################
# load and clean the data
#################
papers = {int(pid): int(year) for pid, year in load_gzip_csv('rawdata/papers.csv.gz')}
cites_list = [(int(p1), int(p2)) for p1, p2 in load_gzip_csv('rawdata/cites.csv.gz')]
print "Read {p} papers and {c} citations".format(p=len(papers), c=len(cites_list))

# Filter out citations where either paper does not have a year
cites_list = [(p1, p2) for p1, p2 in cites_list if p1 in papers and p2 in papers]
print "{c} citations remain after dropping papers with no year".format(c=len(cites_list))

# Filter out bad citations, which go backwards in year
cites_list = [(p1, p2) for p1, p2 in cites_list if papers[p1] >= papers[p2]]
print "{c} citations remain after dropping anachronisms".format(c=len(cites_list))

# Convert cites_list to an adjacency list
cites = defaultdict(list)
for p1, p2 in cites_list:
    cites[p1].append(p2)

###################
# pick a set of seed papers
###################
N = 50
seeds = [pid for pid, year in papers.items() if pid <= N]
print "Chose {s} seed papers (have paper id <= {N})".format(s=len(seeds), N=N)

###################
# find all papers that any seed paper cites at the depth it is first found
###################
citation_depths = dict()
delta = set((p1, p2, 1) for p1 in seeds for p2 in cites[p1])
iteration = 0
while len(delta) > 0:
    print "Iteration {i}, results {r}, delta {d}".format(i=iteration, r=len(citation_depths), d=len(delta))
    for p1, p2, d in delta:
        citation_depths[(p1, p2)] = d

    new_delta = set()
    for (p1, p2, d) in delta:
        for p3 in cites[p2]:
            if (p1, p3) not in citation_depths:
                new_delta.add((p1, p3, d+1))
    delta = new_delta
    
    iteration += 1
print "Iterations {i}, results {r}".format(i=iteration, r=len(citation_depths))

###################
# find papers with a common ancestor
###################
ancestors = defaultdict(list)
for p1, p2 in citation_depths:
    ancestors[p2].append(p1)
print "{a} unique ancestors reachable from seed set".format(a=len(ancestors))

common_cites = defaultdict(list)
for a in ancestors:
    year = papers[a]
    for p1 in ancestors[a]:
        d1 = citation_depths[(p1, a)]
        for p2 in (p2 for p2 in ancestors[a] if p1 < p2):
            d2 = citation_depths[(p2, a)]
            common_cites[(p1, p2)].append((a, max(d1, d2), year))
print "{p} of the {allp} pairs of seed papers have a common ancestor".format(p=len(common_cites), allp=len(seeds)*(len(seeds)-1)/2)

#####################
# resolve the "least common ancestor"
#   The least common ancestor is the ancestor with smallest citation depth and
#   latest year. We break ties by picking the paper with the smallest paper ID.
#####################
def ancestor_key(x):
    a, d, y = x
    return (d, -y, a)
with open('results.csv', 'wb') as resultsfile:
    writer = csv.writer(resultsfile)
    writer.writerow(['p1', 'p2', 'a', 'depth', 'year'])
    for (p1, p2), candidates in sorted(common_cites.items()):
        writer.writerow([p1, p2] + list(min(candidates, key=ancestor_key)))
print "Wrote {r} results to results.csv".format(r=len(common_cites))
