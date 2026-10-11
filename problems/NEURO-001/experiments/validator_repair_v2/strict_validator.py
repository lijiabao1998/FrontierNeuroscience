#!/usr/bin/env python3
"""Finite-scope NEURO-001 synthetic artifact validator. No biological claims.

No imports of baseline.py or its historical reviewer. Known metadata fields are
not scientific evidence; only mathematical payload and protocol identity pass.
"""
import argparse
import functools
import json
import math
import random
from fractions import Fraction as Q
from pathlib import Path

PROTOCOL_SHA256 = '6cd7879947d13de6c7b92b0e91974769157dfbddcef844ed21d8e03a0cac9bfa'
TOLERANCE = 1e-12
METADATA = frozenset(('controls', 'limits', 'author_checks_passed',
    'independent_verification', 'runtime_seconds', 'environment'))


def strict_loads(text):
    def reject_constant(value):
        raise ValueError('Nonfinite JSON literal: ' + value)
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(text, parse_constant=reject_constant,
                      object_pairs_hook=unique_pairs)


def probability(value):
    if isinstance(value, bool) or type(value) not in (Q, int, float):
        raise ValueError('Probability requires rational/integer/finite float')
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError('Nonfinite probability')
    result = Q(value)
    if not 0 <= result <= 1:
        raise ValueError('Probability outside [0,1]')
    return result


def masses(p):
    p = probability(p)
    result = [Q(math.comb(8, k)) * p**k * (1-p)**(8-k) for k in range(9)]
    if sum(result) != 1 or min(result) < 0:
        raise ValueError('Invalid probability distribution')
    return result


def guarded_exact(a, b, t, truth):
    a, b, t = (probability(x) for x in (a, b, t))
    if truth not in ('A', 'B', 'C'):
        raise ValueError('Unknown truth label')
    ma, mb, mt = (masses(p) for p in (a, b, t))
    if any(x+y == 0 for x, y in zip(ma, mb)):
        raise ValueError('Undefined candidate posterior at a response count')
    post = [x/(x+y) for x, y in zip(ma, mb)]
    score_a = [Q(1) if x>y else Q(0) if x<y else Q(1,2) for x,y in zip(ma,mb)]
    recovery = (sum(p*(s if truth=='A' else 1-s) for p,s in zip(mt,score_a))
                if truth != 'C' else None)
    confidence = sum(p for p, q in zip(mt, post) if max(q,1-q) >= Q(19,20))
    return {'recovery_fraction':str(recovery) if recovery is not None else None,
            'recovery':float(recovery) if recovery is not None else None,
            'mean_posterior_A':float(sum(p*q for p,q in zip(mt,post))),
            'high_confidence':float(confidence),
            'high_confidence_fraction':str(confidence),
            'binomial_mass':[str(p) for p in mt]}


def information(a, b, n):
    a, b = probability(a), probability(b)
    terms = []
    for k in range(n+1):
        la = Q(math.comb(n,k))*a**k*(1-a)**(n-k)
        lb = Q(math.comb(n,k))*b**k*(1-b)**(n-k)
        mixture = (la+lb)/2
        for mass in (la, lb):
            if mass:
                terms.append(float(mass/2)*math.log2(float(mass/mixture)))
    return math.fsum(terms)


def predictions(x):
    return (2+x)/4, (2+abs(x))/4


@functools.lru_cache(maxsize=1)
def expected_payload():
    """Deterministic frozen calculation, never reading a submitted result."""
    grid = [Q(i,4) for i in range(-4,5)]
    scores = [information(*predictions(x),1) for x in grid]
    selected = next(x for x,s in zip(grid,scores) if max(scores)-s <= 1e-14)
    result = {'protocol_sha256':PROTOCOL_SHA256, 'selected_x':str(selected),
        'grid':[{'x':str(x),'eig1':s} for x,s in zip(grid,scores)],
        'configurations':60, 'designs':[], 'mc':[], 'pooled_mc':[]}
    for di,(name,x) in enumerate((('ordinary',Q(1,2)),('diagnostic',selected))):
        a,b = predictions(x)
        design = {'name':name,'x':str(x),'pA':str(a),'pB':str(b),
                  'eig8':information(a,b,8),'truths':{}}
        ma,mb = masses(a),masses(b)
        post = [u/(u+v) for u,v in zip(ma,mb)]
        score_a = [Q(1) if u>v else Q(0) if u<v else Q(1,2) for u,v in zip(ma,mb)]
        for ti,(truth,t) in enumerate((('A',a),('B',b),('C',Q(1,2)))):
            design['truths'][truth] = guarded_exact(a,b,t,truth)
            for si in range(10):
                seed = 10000+100*di+10*ti+si
                rng = random.Random(seed)
                hist = [0]*9
                for sequence in range(1000):
                    k = 0
                    for draw in range(8):
                        k += int(rng.random() < float(t))
                    hist[k] += 1
                recovery = (sum(c*float(s if truth=='A' else 1-s)
                                for c,s in zip(hist,score_a))/1000
                            if truth != 'C' else None)
                high = sum(c for c,q in zip(hist,post) if max(q,1-q)>=Q(19,20))/1000
                result['mc'].append({'design':name,'truth':truth,'seed':seed,
                    'histogram':hist,'recovery':recovery,'high_confidence':high})
        design['equal_prior_recovery'] = (design['truths']['A']['recovery']+
                                          design['truths']['B']['recovery'])/2
        result['designs'].append(design)
    for d in result['designs']:
        for truth,exact in d['truths'].items():
            rows = [r for r in result['mc'] if r['design']==d['name'] and r['truth']==truth]
            for metric in ('recovery','high_confidence'):
                if exact[metric] is None:
                    continue
                estimate = sum(r[metric] for r in rows)/10
                result['pooled_mc'].append({'design':d['name'],'truth':truth,
                    'metric':metric,'estimate':estimate,'exact':exact[metric],
                    'abs_error':abs(estimate-exact[metric])})
    return result


def compare(got, expected, path='$'):
    if isinstance(expected, dict):
        if type(got) is not dict or set(got) != set(expected):
            raise ValueError(path+': wrong object fields')
        for key,value in expected.items():
            compare(got[key],value,path+'.'+key)
    elif isinstance(expected, list):
        if type(got) is not list or len(got)!=len(expected):
            raise ValueError(path+': wrong array shape')
        for index,(a,b) in enumerate(zip(got,expected)):
            compare(a,b,path+'['+str(index)+']')
    elif type(expected) is float:
        if type(got) not in (int,float) or not math.isfinite(got):
            raise ValueError(path+': expected finite numeric value')
        if abs(got-expected) > TOLERANCE:
            raise ValueError(path+': numerical mismatch')
    elif type(got) is not type(expected) or got != expected:
        raise ValueError(path+': exact value/type mismatch')


def validate_report(report):
    if type(report) is not dict:
        raise ValueError('Report must be an object')
    expected = expected_payload()
    if not set(expected) <= set(report) <= set(expected)|METADATA:
        raise ValueError('Unexpected or missing top-level fields')
    compare({k:report[k] for k in expected}, expected)
    return {'mathematical_payload':'PASS', 'metadata_claims':'NOT_VALIDATED',
            'scientific_claim':'NONE', 'historical_acceptance':'FAILED/INCOMPLETE'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    report = strict_loads(args.report.read_text())
    print(json.dumps(validate_report(report),sort_keys=True,allow_nan=False))


if __name__ == '__main__':
    main()
