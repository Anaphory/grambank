
import sys
import os

from clld.scripts.util import initializedb, Data
from clld.db.meta import DBSession
from clld.db.models import common
from clld.db.util import compute_language_sources
from clld_glottologfamily_plugin.models import Family
from clld_glottologfamily_plugin.util import load_families
from pyglottolog.api import Glottolog

import grambank
from grambank.scripts.util import (
    import_features_collaborative_sheet, import_cldf, get_clf_paths, get_name,
    GRAMBANK_REPOS,
)

from stats_util import grp, feature_stability, feature_dependencies, dependencies_graph, deep_families, havdist
from grambank.models import Dependency, Transition, Stability, DeepFamily, Support, HasSupport, Feature


def main(args):
    data = Data()
    dataset = common.Dataset(
        id=grambank.__name__,
        name="GramSunDa",
        publisher_name="Leiden University Centre for Linguistics",
        publisher_place="Leiden",
        publisher_url="https://www.universiteitleiden.nl/en/humanities/leiden-university-centre-for-linguistics",
        license="NONE", #"http://creativecommons.org/licenses/by/4.0/",
        domain='gramsunda.marianklamer.org',
        contact='g.a.kaiping@hum.leidenuniv.nl',
        jsondata={
            'license_icon': 'cc-by.png',
            'license_name': 'No license yet'}) # Creative Commons Attribution 4.0 International License'})
    DBSession.add(dataset)

    import_features_collaborative_sheet(GRAMBANK_REPOS, data)
    import_cldf(os.path.join(GRAMBANK_REPOS, 'datasets'), data)
    ##import_cldf("C:\\python27\\dbs\\bwohh\\", data, add_missing_features = True)

    load_families(
        data,
        list(data['GrambankLanguage'].values()),
        isolates_icon='tcccccc')

    return 

def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodically whenever data has been updated.
    """
    compute_language_sources()
    return 
    from time import time
    _s = time()

    def checkpoint(s, msg=None):
        n = time()
        print(n - s, msg or '')
        return n

    sql = """
select p.id, l.id, v.name from value as v, valueset as vs, language as l, parameter as p
where v.valueset_pk = vs.pk and vs.language_pk = l.pk and vs.parameter_pk = p.pk
    """
    datatriples = [(v[0], v[1], v[2]) for v in DBSession.execute(sql)]
    _s = checkpoint(_s, '%s values loaded' % len(datatriples))

    flv = dict([(feature, dict(lvs)) for (feature, lvs) in grp(datatriples).items()])
    _s = checkpoint(_s, 'triples grouped')

    clfps = list(get_clf_paths([row[0] for row in DBSession.execute("select id from language")]))
    _s = checkpoint(_s, '%s clfps loaded' % len(clfps))

    features = {f.id: f for f in DBSession.query(Feature)}
    for (f, lv) in flv.items():
        features[f].representation = len(lv)
    DBSession.flush()
    _s = checkpoint(_s, 'representation assigned')

    families = {f.id: f for f in DBSession.query(Family)}
    if False:
        fs = feature_stability(datatriples, clfps)
        _s = checkpoint(_s, 'feature_stability computed')

        for (f, (s, transitions, stationarity_p, synchronic_p)) in fs:
            print(f)
            stability = Stability(
                id=f.replace("GB", "S"),
                feature=features[f],
                parsimony_stability_value=s["stability"],
                parsimony_retentions=s["retentions"],
                parsimony_transitions=s["transitions"],
                jsondata={'diachronic_p': stationarity_p, "synchronic_p": synchronic_p})
            DBSession.add(stability)
            for (i, (fam, (fromnode, tonode), (ft, tt))) in enumerate(transitions):
                DBSession.add(Transition(
                    id="%s: %s->%s" % (f, fromnode, tonode),
                    stability=stability,
                    fromnode=get_name(fromnode),
                    tonode=get_name(tonode),
                    fromvalue=ft,
                    tovalue=tt,
                    family=families[fam],
                    retention_innovation="Retention" if ft == tt else "Innovation"))
        DBSession.flush()
        _s = checkpoint(_s, 'stability and transitions loaded')

    imps = feature_dependencies(datatriples)
    _s = checkpoint(_s, 'feature_dependencies computed')
    if True:
        (H, V) = dependencies_graph([(v, f1, f2) for ((v, dstats), f1, f2) in imps])
        _s = checkpoint(_s, 'dependencies_graph written')

        for (i, ((v, dstats), f1, f2)) in enumerate(imps):
            combinatory_status = ("primary" if (f1, f2) in H else ("epiphenomenal" if v > 0.0 else None)) if H else "N/A"
            DBSession.add(Dependency(
                id="%s->%s" % (f1, f2),
                strength=v,
                feature1=features[f1],
                feature2=features[f2],
                representation=dstats["representation"],
                combinatory_status=combinatory_status,
                jsondata=dstats))
        DBSession.flush()
        _s = checkpoint(_s, 'dependencies loaded')

    coordinates = {
        lg.id: (lg.longitude, lg.latitude)
        for lg in DBSession.query(common.Language)
        .filter(common.Language.longitude != None)
        .filter(common.Language.latitude != None)}
    deepfams = deep_families(datatriples, clfps, coordinates=coordinates)
    _s = checkpoint(_s, '%s deep_families computed' % len(deepfams))

    missing_families = set()
    data = Data()
    for ((l1, l2), support_value, significance, supports, f1c, f2c) in deepfams:
        dname = "proto-%s x proto-%s" % (glottolog_names[l1], glottolog_names[l2])
        kmdistance = havdist(f1c, f2c)
        (f1lon, f1lat) = f1c if f1c else (None, None)
        (f2lon, f2lat) = f2c if f2c else (None, None)

        for li in [l1, l2]:
            if li not in families:
                missing_families.add(li)

        deepfam = DeepFamily(
            id=dname,
            support_value=support_value,
            significance=significance,
            family1=families.get(l1),
            family2=families.get(l2),
            family1_latitude = f1lat,
            family1_longitude = f1lon,
            family2_latitude = f2lat,
            family2_longitude = f2lon,
            geographic_plausibility = kmdistance)
        DBSession.add(deepfam)
        for (f, v1, v2, historical_score, independent_score, support_score) in supports:
            vid = ("%s: %s %s %s" % (f, v1, "==" if v1 == v2 else "!=", v2)).replace(".", "")
            #vname = ("%s|%s" % (v1, v2)).replace(".", "")
            #print vid, vname
            if vid not in data["Support"]:
                data.add(
                    Support, vid,
                    id = vid,
                    historical_score = historical_score,
                    independent_score = independent_score,
                    support_score = support_score,
                    value1= v1,
                    value2 = v2,
                    feature=features[f])
            DBSession.add(HasSupport(
                id=dname + "-" + vid,
                deepfamily = deepfam,
                support = data["Support"][vid]))
    print('missing_families:')
    print(missing_families)
    DBSession.flush()
    _s = checkpoint(_s, 'deep_families loaded')

    compute_language_sources()


if __name__ == '__main__':
    initializedb(create=main, prime_cache=prime_cache)
    sys.exit(0)

