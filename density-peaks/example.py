import csv
import gzip
from math import sqrt
import sys


def load_gzip_csv(filename):
    """Helper function to load CSV data from a GZipped file"""
    gzfile = gzip.GzipFile(filename, 'rb')
    csvfile = csv.reader(gzfile)
    header_line = csvfile.next()
    print 'Reading from CSV file {fn} with headers {h}'.format(fn=filename, h=header_line)
    return csvfile

###################
# Problem constants
###################
# To make the data small, we will keep only N cells
N = 5000
# Cutoff distance dc of a cluster
dc = 2000
# Number of output clusters
C = 5

##################
# load the data
#################
cells = {}
for Cruise, Day, File_Id, Cell_Id, fsc_small, chl_small, pe, pop in load_gzip_csv('rawdata/big_data.csv.gz'):
    # We have enough cells
    if len(cells) >= N:
        break
    # SeaFlow constraint: points with low chlorophyll are not biological; skip
    if int(chl_small) < 10000:
        continue
    # Save the spectral data on each particle
    cells[int(Cell_Id)] = (int(fsc_small), int(chl_small), int(pe))
print 'Read {C} cells into memory'.format(C=len(cells))

#############################
# Compute all-pairs distances
#############################
def dist(a, b):
    return sqrt(sum((x-y)**2 for x, y in zip(a, b)))
dists = {(i, j): dist(cells[i], cells[j])
         for i in cells
         for j in cells}
print 'Distances computed between {D} unique pairs of points'.format(D=len(dists))

#################################
# Compute density for every point
#################################
while True:
    total_density = 0
    density = {i: sum(1 for j in cells if i != j and dists[(i, j)] < dc)
               for i in cells}
    print 'Densities computed for {N} points; dc={dc}'.format(N=len(density), dc=dc)
    avg_density = float(sum(v for v in density.values())) / len(cells)
    # Paper says to find a dc that makes avg density between 1 and 2% of nodes
    if avg_density < len(cells) * 0.01:
        dc *= 1.5
    elif avg_density > len(cells) * 0.02:
        dc /= 2
    else:
        break

#################################################
# Compute delta-i, the dist to a more dense point
#################################################
delta = {}
for i in cells:
    try:
        delta[i] = min(dists[(i, j)]
                       for j in cells
                       if density[j] > density[i])
    except ValueError:
        # This will only happen for the "most dense" points. Take
        # the max distance by convention
        delta[i] = max(dists[(i, j)] for j in cells)
print "Computed deltas for {N} points".format(N=len(delta))

#################################################
# Use the top C points in delta*density for centers
#################################################
gamma = sorted(((i, density[i] * delta[i]) for i in cells),
               key=lambda (i, g): (-g, i))
# Cell ID: cluster
clusters = {g[0]: i for i, g in enumerate(gamma[:C])}

#################################################
# Assign all remaining points to clusters
#################################################
for i in cells:
    if i in clusters: continue
    (min_d, min_j) = min((dists[(i, j)], j) for j in clusters)
    clusters[i] = clusters[min_j]

#################################################
# Assign all remaining points to clusters
#################################################
print >> sys.stderr, "i\tclust\tfsc\tchl\tpe"
for i in clusters:
    print >> sys.stderr, "{i}\t{clust}\t{fsc}\t{chl}\t{pe}".format(i=i, clust=clusters[i], fsc=cells[i][0], chl=cells[i][1], pe=cells[i][2])