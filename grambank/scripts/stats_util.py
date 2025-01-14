from itertools import chain
import math

from clldutils.path import Path

import grambank


uchar = '?'
undefined = {}
undefined['?'] = uchar
undefined['n/a'] = uchar
undefined['N/A'] = uchar
undefined['n.a.'] = uchar
undefined['n.a'] = uchar
undefined['N.A.'] = uchar
undefined['N.A'] = uchar
undefined['-'] = uchar
undefined[''] = uchar
undefined[None] = uchar
undefined[()] = uchar
undefined["NODATA"] = uchar
undefined['? - Not known'] = uchar

dottemplate = """digraph G {
%s
}
"""
def dot(H, V = []):
    return dottemplate % ''.join(['   %s -> %s [label="%.2f"];\n' % (f1, f2, v) for ((f1, f2), v) in H.items()] + ['   %s;\n' % f for f in V])



def haversine(xxx_todo_changeme, xxx_todo_changeme1):
    (lon1, lat1) = xxx_todo_changeme
    (lon2, lat2) = xxx_todo_changeme1
    R = 6371 # km

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = (math.sin(dlat/2)**2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c

    return d

def havdist(c1, c2):
    if None in (c1, c2):
        return None
    return haversine(c1, c2)

def avg(xs):
    return sum(xs)/float(len(xs))

def argm(d, f = max):
    if len(d) == 0:
        return None
    (v, m) = f([(v, k) for (k, v) in d.items()])
    return m


def fd(ws):
    d = {}
    for w in ws:
        d[w] = d.get(w, 0) + 1
    return d

def norm(d):
    z = float(sum(d.values()))
    if z == 0.0:
        return dict([(k, 0.0) for (k, _) in d.items()])
    return dict([(k, x/z) for (k, x) in d.items()])


def allmax(d, f=max):
    if not d:
        return {}
    mv = f(iter(d.values()))
    return dict([(k, v) for (k, v) in d.items() if v == mv])


def pairs(xs):
    return [(x, y) for x in xs for y in xs if x < y]

def grp(l):
    def sdl(d, k, v):
        if k in d:
            d[k][len(d[k])] = v
        else:
            d[k] = {0: v}
    r = {}
    for x in l:
        sdl(r, x[0] if x else None, x[1:])
    return dict([(k, list(vs.values())) for (k, vs) in r.items()])    

def grp2(l):
    def sdl(d, k, v):
        if k in d:
            d[k][len(d[k])] = v
        else:
            d[k] = {0: v}
    r = {}
    for (x, y) in l:
        sdl(r, x, y)
    return dict([(k, list(vs.values())) for (k, vs) in r.items()])    


#def grp(xs):
#    return dict([(g, [tup[1:] for tup in tups]) for (g, tups) in groupby(xs, lambda x: x[0])])

def leaves(d):
    if not d:
        return set()
    l = set([k for (k, v) in d.items() if not v])
    return l.union(chain(*[leaves(v) for (k, v) in d.items() if v]))

def paths_to_d(pths):
    if pths == [()] or pths == [[]]:
        return None
    return dict([(p, paths_to_d(tails)) for (p, tails) in grp(pths).items()])


def levpairs(pths):
    def lev(p1, p2):
        r = {node: i for (i, node) in enumerate(reversed(p1))}
        for (i, node) in enumerate(reversed(p2)):
            if node in r:
                return max(i, r[node])
        return None
    lgp = {p[-1]: p[:-1] for p in pths}
    return {(l1, l2): lev(lgp[l1], lgp[l2]) for (l1, l2) in pairs(list(lgp.keys()))}


def sumds(ds):
    r = {}
    for (i, v) in chain(*[iter(d.items()) for d in ds]):
        r[i] = r.get(i, 0) + v
    return r

def stability_tp(lv, fp):
    ftp = {}
    for (fam, famt) in fp.items():
        if not leaves({fam: famt}).intersection(lv):
            continue
        (t, pr) = prr(fam, lv, fp)
        if not t:
            continue
        tr = transitions(t)
        ftp[fam] = [((tf, tt), (pr[tf], pr[tt])) for (tf, tt) in tr]
    return ftp        

def prune(d, lvs):
    if not d:
        return d
    ls = [(k, v) for (k, v) in d.items() if not v and k in lvs]
    sdl = [(k, prune(v, lvs)) for (k, v) in d.items() if v]
    return dict(ls + [(k, v) for (k, v) in sdl if v and len(v) != 1] + [(a, b) for (k, v) in sdl if v and len(v) == 1 for (a, b) in v.items()])


def prr(f, a, fp):
    dlgs = leaves(fp.get(f, dict.fromkeys(a))).intersection([lg for (lg, v) in a.items() if v not in undefined])
    t = prune({f: fp.get(f, dict.fromkeys(a))}, dlgs)
    done = parsimony_reconstruct(t, a)
    r = dict([(k, v) for (k, v) in a.items() if k in dlgs])
    for (n, rd) in done.items():
        r[n] = '/'.join(list(allmax(rd, min).keys()))
    return (t, r)

def transitions(t):
    if not t:
        return []
    thislev = [(k, kp) for (k, v) in t.items() if v for kp in list(v.keys())]
    return thislev + [ti for (k, v) in t.items() if v for ti in transitions(v)]

def trcount(tp):
    tpc = [[(tfi, tti) for tfi in tf.split("/") for tti in tt.split("/")] for (tf, tt) in tp]
    s = {}
    for (k, v) in [((tfi, tti), 1/float(len(tpci))) for tpci in tpc for (tfi, tti) in tpci]:
        s[k] = s.get(k, 0) + v
    return s

#def stability_ftp(lv, fp):
#    return dict([(l, trcount([(tf, tt) for (label, (tf, tt)) in labeled_tr])) for (l, labeled_tr) in stability_tp(lv, fp).iteritems()])

def stability_ftp(lv, fp):
    return [(l, label, tft) for (l, labeled_tr) in stability_tp(lv, fp).items() for (label, tft) in labeled_tr]

def transition_counts_to_matrix(u):
    kall = set([k for ks in u.keys() for k in ks])
    ks = dict([(k1, norm(dict([(k2, u.get((k1, k2), 0)) for k2 in kall]))) for k1 in kall])
    return ks
    
def mmul(u1, u2):
    kall = list(u1.keys())
    return dict([(k1, dict([(k2, sum([u1[k1][m]*u2[m][k2] for m in kall])) for k2 in kall])) for k1 in kall])

def mrow_diff(r1vs, r2vs):
    u = set(list(r1vs.keys()) + list(r2vs.keys()))
    return sum([(r1vs.get(x, 0.0)-r2vs.get(x, 0.0))**2 for x in u])
    
def stationary(m, epsilon = 0.0001):
    if not m:
        return []
    def stationary_diff(mtx):
        return sum([mrow_diff(mtx[r1], mtx[r2]) for (r1, r2) in pairs(iter(mtx.keys()))])
        
    ms = m
    while stationary_diff(ms) >= epsilon:
        ms = mmul(ms, m)
    return list(ms.values())[0]

def synchronic(lv, d):
    if not lv:
        return {}
    leaves = [{lv[k]: 1.0} for (k, v) in d.items() if (not v) and k in lv]
    branches = [vp for vp in [synchronic(lv, v) for (k, v) in d.items() if v] if vp]
    return {k: v/len(leaves+branches) for (k, v) in sumds(leaves + branches).items()}
    
def feature_stability(datatriples, clfps):
    clf = paths_to_d(clfps)
    flv = dict([(feature, dict(lvs)) for (feature, lvs) in grp(datatriples).items()])
    return [(f, parsimony_stability(lv, clf)) for (f, lv) in flv.items()]

def parsimony_stability(lv, fp):
    transitions = stability_ftp(lv, fp)
    u = trcount([tft for (f, label, tft) in transitions])    
    stability = sum([v for ((a, b), v) in u.items() if a == b])
    total = float(sum(u.values()))
    r = {"retentions": stability, "transitions": total}
    r["stability"] = stability/total if total > 0 else None
    stationarity_p = stationary(transition_counts_to_matrix(u))
    synchronic_p = synchronic(lv, fp)
    return (r, transitions, stationarity_p, synchronic_p)

def parsimony_reconstruct(fp, r):
    done = {}
    def rec(d):
        if not d:
            return None
        t = {}
        for (k, v) in d.items():
            if k in done:
                t[k] = done[k]
                continue
            if v:
                t[k] = rec(v)
                done[k] = t[k]
                continue
            if k in r and r[k] != "NODATA": #TODO
                t[k] = {r[k]: 0}

        tvals = [x for x in list(t.values()) if x != None]
        if not tvals:
            return None
        return dict([(k, sum([min(d.get(k, 1), 1+min(d.values())) for d in tvals])) for k in types])
    types = set(r.values())
    rd = rec(fp)
    return done #allmax(rd, min)

def location_reconstruct(fp, r):
    done = {}
    def rec(d):
        if not d:
            return None
        t = {}
        for (k, v) in d.items():
            if k in done:
                t[k] = done[k]
                continue
            if v:
                t[k] = rec(v)
                done[k] = t[k]
                continue
            if k in r:
                t[k] = r[k]
                done[k] = t[k]
                continue

        tvals = [x for x in list(t.values()) if x != None]
        if not tvals:
            return None
        return (avg([x for (x, y) in tvals]), avg([y for (x, y) in tvals])) #Replace by point of minimum distance or sthng like that
    rd = rec(fp)
    return rd


def lg(z):
    if z == 0:
        return 0.0
    return math.log(z, 2)

def ent(pij, pi, pj):
    return pij*lg(pij/(pi*pj))

def entp(pd):
    return -sum([px * lg(px) for px in pd.values()])

def I(X, Y, XY):    
    I = sum([ent(XY.get((x, y), 0), px, py) for (x, px) in X.items() for (y, py) in Y.items()])
    return I

#E.g. X = {L1: 'a', L2: 'a'} Y = {L1: 'a', L2: 'b'}
def implies(xxx_todo_changeme2):
    (X, Y) = xxx_todo_changeme2
    ((x, y, xy), dstats) = jnt(X, Y)
    (strength, istats) = pi(x, y, xy)
    return (strength, dict(list(dstats.items()) + list(istats.items())))
    
def percent(k, n):
    return "%.1f" % (100*(k/float(n))) + "%"

def vtable(f):
    n = sum(f.values())
    return [k + (f[k], percent(f[k], n)) if type(k) == type(()) else (k, f[k], percent(f[k], n)) for k in sorted(f.keys())] + [("Total",) + tuple(["" for i in range(1, max([len(k) if type(k) == type(()) else 1 for k in f.keys()] + [0]))]) + (n, "")]
    
def jnt(X, Y):
    U = set(X.keys()).intersection(Y)
    XY = dict([(z, (X[z], Y[z])) for z in U])
    fx = fd([X[z] for z in U])
    fy = fd([Y[z] for z in U])
    fxy = fd([XY[z] for z in U])
    x = norm(fx)
    y = norm(fy)
    xy = norm(fxy)
    dstats = {"f1stats": vtable(fx), "f2stats": vtable(fy), "f1f2stats": vtable(fxy), "representation": len(U)}
    return ((x, y, xy), dstats)

def pi(X, Y, XY):
    i = I(X, Y, XY) 
    iy = entp(Y)
    strength = i/iy if iy != 0.0 else 0.0
    istats = {"f1h": entp(X), "f2h": iy, "f1f2h": entp(XY), "f1f2mi": i}
    return (strength, istats)

def has_cycle(G):
    def find_cycle_to_ancestor(node, ancestor):
        """
        Find a cycle containing both node and ancestor.
        """
        path = []
        while (node != ancestor):
            if (node is None):
                return []
            path.append(node)
            node = spanning_tree[node]
        path.append(node)
        path.reverse()
        return path
   
    def dfs(node):
        """
        Depht-first search subfunction.
        """
        visited[node] = 1
        # Explore recursively the connected component
        for each in graph.get(node, []):
            if (cycle):
                return
            if (each not in visited):
                spanning_tree[each] = node
                dfs(each)
            else:
                cycle.extend(find_cycle_to_ancestor(node, each))

    graph = dict([(k, dict(vs)) for (k, vs) in grp2([(x, (y, v)) for ((x, y), v) in G.items()]).items()])
    visited = {}              # List for marking visited and non-visited nodes
    spanning_tree = {}        # Spanning tree
    cycle = []

    # Algorithm outer-loop
    for each in graph:
        # Select a non-visited node
        if (each not in visited):
            spanning_tree[each] = None
            # Explore node's connected component
            dfs(each)
            if (cycle):
                return cycle
    return None


#MSTs = [GT(edmonds.mst(x, G)) for x in fr.keys() if G.has_key(x)]
def mst(G, r, it = 0):
    def contract(G, c, it):
        cnodes = set([x for p in list(c.keys()) for x in p])
        Gc = dict([((x, y), v) for ((x, y), v) in G.items() if (x not in cnodes) and (y not in cnodes)])
        VC = set([x for p in list(G.keys()) for x in p]).difference(cnodes)
        octrack = {}
        for v in VC:
            oc = [(G[cx, v], cx) for cx in cnodes if (cx, v) in G]
            if oc:
                Gc['C' + str(it), v] = max(oc)[0]
                octrack[v] = max(oc)[1]

        ictrack = {}
        for v in VC:
            ic = [(G[v, cx] - G[[y for (y, z) in list(c.keys()) if z == cx][0], cx] + sum(c.values()), cx) for cx in cnodes if (v, cx) in G]
            if ic:
                Gc[v, 'C' + str(it)] = max(ic)[0]
                ictrack[v] = max(ic)[1]
        return (Gc, octrack, ictrack)
    #Chu-Liu-Edmonds(G, s)
    #Graph G = (V,E)
    #Edge weight function s : E \to R
    I = dict([(k, dict(vs)) for (k, vs) in grp2([(y, (x, v)) for ((x, y), v) in G.items()]).items()])
    M = [(argm(ixs), x) for (x, ixs) in I.items()]
    GM = dict([((u, v), G[(u, v)]) for (u, v) in M if v != r])
    #print "Iter", it
    #print "G nodes", len(setall(G.keys())), "edges", len(G)
    #print "GM nodes", len(setall(GM.keys())), "edges", len(GM)
    clist = has_cycle(GM)
    #print "trying", GM
    if not clist:
        #print "OK"
        return GM
    #print "cycle found", clist
    #print
    
    ces = [(clist[i], clist[i+1]) for i in range(len(clist)-1)] + [(clist[-1], clist[0])]
    c = dict([(k, G[k]) for k in ces])
    (Gc, octrack, ictrack) = contract(G, c, it)
    #print G, "contracted to", Gc
    #print "itrack", ictrack
    #print "otrack", octrack
    #if not Gc:
    #    weak = argm(GM, min)
    #    Y = dict([(edge, G[edge]) for edge in M if edge != weak])
    #    return Y
    #else:
    Y = mst(Gc, r, it + 1)
    #print it, "Tree edges", len(setall(Y.keys())), "from", len(setall(Gc.keys()))
    #xs = [([(xpp, ex) for (xpp, ex) in c.keys() if ex == x], x) for (xp, x) in Y.keys()]
    #(xpp, x) = [(xpp[0], x) for (xpp, x) in xs if xpp][0]

    U = dict([((x, y), v) for ((x, y), v) in Y.items() if x != ('C'+ str(it)) and y != ('C' + str(it))])
    #print "All edges except contracted item", 'C' + str(it), U
    intoc = [x for ((x, y), v) in Y.items() if y == 'C' + str(it)]
    #print "Intoc", [x for ((x, y), v) in Y.iteritems() if y == 'C' + str(it)]
    outoc = [y for ((x, y), v) in Y.items() if x == 'C' + str(it)]
    #print it, "Reconstructing", len(U), "outside cycle", intoc, outoc
    #print intoc, ictrack[intoc], octrack[outoc], outoc
    #print
    if intoc:
        U[intoc[0], ictrack[intoc[0]]] = G[intoc[0], ictrack[intoc[0]]]
    if outoc:
        U[octrack[outoc[0]], outoc[0]] = G[octrack[outoc[0]], outoc[0]]

    for x in intoc:
        U[x, ictrack[x]] = G[x, ictrack[x]]
    for y in outoc:
        U[octrack[y], y] = G[octrack[y], y]
    for ((x, y), v) in c.items():
        U[x, y] = v

    for (x, y) in c.keys():
        if [(xpp, z) for (xpp, z) in U.keys() if z == y and xpp != x]:
            del U[x, y]
            break
    else:
        print("ERROR NO KICKOUT", c)
    return U


def both_defined(lv1, lv2):
    u = [x for x in set(lv1.keys()).intersection(iter(lv2.keys())) if lv1[x] not in undefined and lv2[x] not in undefined] 
    return (dict([(x, lv1[x]) for x in u]), dict([(x, lv2[x]) for x in u])) 

def feature_dependencies(datatriples):
    flv = dict([(feature, dict(lvs)) for (feature, lvs) in grp(datatriples).items()])
    imps = [(implies(both_defined(lv1, lv2)), f1, f2) for (f1, lv1) in flv.items() for (f2, lv2) in flv.items() if f1 != f2]
    return imps

def dependencies_graph(imps):
    deps = dict([((f1, f2), v) for (v, f1, f2) in imps if v > 0.0])
    V = set([f for fs in deps.keys() for f in fs])
    G = dict([(k, v) for (k, v) in list(deps.items()) if v > 0.0])
    MSTs = [mst(G, x) for x in V]
    (mv, H) = (float("-inf"), None)
    for H in MSTs:
        if sum(H.values()) > mv:
            (mv, H) = (sum(H.values()), H)
    #W = dict([(y, 1.0-v) for ((x, y), v) in H.iteritems()])
    #sav(dot(H, V), 'grambank_mst.gv')
    path = Path(grambank.__file__).parent.joinpath('static', 'dependencies.gv')
    with open(path.as_posix(), 'w') as fp:
        fp.write(dot(H, V))

    return (H, V) #dot(H, V)


def sscmp(fv1, fv2, fsynp, fstab):
    def overlap(vs1, vs2):
        a = set(vs1.split("/"))
        b = set(vs2.split("/"))
        return len(a.intersection(b))/float(len(a.union(b)))
    
    (lv1, lv2) = both_defined(fv1, fv2)
    fs = set(list(lv1.keys()) + list(lv2.keys()))
    ss = [(f, lv1[f], lv2[f], fstab[f], max(sum([fsynp[f].get(v, 0.0) for v in lv1[f].split("/")]), sum([fsynp[f].get(v, 0.0) for v in lv1[f].split("/")]))) for f in fs]
    supports = [(f, v1, v2, historical_score, independent_score, (historical_score-independent_score)*overlap(v1, v2)) for (f, v1, v2, historical_score, independent_score) in ss]
    pts = sum([pt for (f, v1, v2, historical_score, independent_score, pt) in supports])
    return (float(pts)/len(ss) if len(ss) > 0 else 0.0, supports)

def deep_families(datatriples, clfps, coordinates = {}):
    fstability = feature_stability(datatriples, clfps)
    fstab = {f: s["stability"] for (f, (s, transitions, stationarity_p, synchronic_p)) in fstability}
    fsynp = {f: synchronic_p for (f, (s, transitions, stationarity_p, synchronic_p)) in fstability}
    
    flv = dict([(feature, dict(lvs)) for (feature, lvs) in grp([(f, l, v) for (f, l, v) in datatriples if v not in undefined]).items()])
    lfv = dict([(l, dict(fs)) for (l, fs) in grp([(l, f, v) for (f, l, v) in datatriples if v not in undefined]).items()])

    clf = paths_to_d(clfps)
    clfc = {pth[-1]: pth[:-1] for pth in clfps}
    
    famlgs = grp2([(clfc[lg][0] if clfc[lg] else lg, lg) for lg in lfv.keys()])
    famts = dict([(fam, {fam: prune(clf.get(fam, dict.fromkeys(lgs)), lgs)}) for (fam, lgs) in list(famlgs.items())])
    #print famts["bilu1245"], famlgs["bilu1245"], clf["bilu1245"]
    protolfv = dict([(fam, protofs(t, lfv, list(flv.keys()), famlgs[fam])) for (fam, t) in famts.items()])
    #print protolfv["bilu1245"]
    #print lfv["bilu1245"]

    l1l2s = [((l1, l2), sscmp(lfv[l1], lfv[l2], fsynp, fstab)[0]) for ((l1, l2), lev) in levpairs(clfps).items() if lev == 0 and l1 in lfv and l2 in lfv]
    dfs = dict([((l1, l2), sscmp(protolfv[l1], protolfv[l2], fsynp, fstab)) for (l1, l2) in pairs(list(protolfv.keys()))])
    t = float(len(l1l2s))
    
    dfsig = {pair: len([1 for (_, ssl) in l1l2s if ssv > ssl])/t for (pair, (ssv, supports)) in dfs.items()}

    return [((l1, l2), ssv, dfsig[(l1, l2)], supports, location_reconstruct(famts[l1], coordinates), location_reconstruct(famts[l2], coordinates)) for ((l1, l2), (ssv, supports)) in dfs.items()]
    
def proto(t, lv):
    [root] = list(t.keys())
    if root in lv:
        return lv[root]
    done = parsimony_reconstruct(t, lv)
    if root in done and done[root]:
        return "/".join(list(allmax(done[root], min).keys()))
    return None

def protofs(t, lfs, fs, lgs):
    r = {}
    for f in fs:
        a = dict([(lg, lfs[lg][f]) for lg in lgs if f in lfs[lg]])
        p = proto(t, a)
        if p:
            r[f] = p
    return r

def deslashcount(r):
    return {k: sum(vs) for (k, vs) in grp2([(x, 1.0/len(xs.split("/"))) for xs in list(r.values()) for x in xs.split("/")]).items()}
