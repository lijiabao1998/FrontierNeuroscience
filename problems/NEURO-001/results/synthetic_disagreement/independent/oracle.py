#!/usr/bin/env python3
"""Independent NEURO-001 oracle: ordered-response enumeration, not binomial formula.
Written from the frozen protocol before reading author source or outputs.
Python standard library only; no author modules are imported.
"""
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
import argparse, hashlib, json, math, platform, random, sys, time

PIN = '6cd7879947d13de6c7b92b0e91974769157dfbddcef844ed21d8e03a0cac9bfa'
GRID = tuple(Q(i,4) for i in range(-4,5))
N = 8

def require_probability(p):
    if not isinstance(p,Q) or not 0 <= p <= 1:
        raise ValueError('Probability must be a finite rational in [0,1]')
    return p

def probabilities(x):
    if not isinstance(x,Q) or not -1 <= x <= 1:
        raise ValueError('Input must be a finite rational in [-1,1]')
    return (Q(2)+x)/4, (Q(2)+abs(x))/4

def sequence_probability(p, seq):
    require_probability(p)
    v = Q(1)
    for y in seq:
        if type(y) is not int or y not in (0,1):
            raise ValueError('Response must be 0 or 1')
        v *= p if y else 1-p
    return v

def enumerate_design(pa,pb,n=8):
    require_probability(pa); require_probability(pb)
    if type(n) is not int or not 1 <= n <= 8:
        raise ValueError('This oracle covers integer sequence length 1..8')
    mass = {t:[Q(0)]*(n+1) for t in ('A','B','C')}
    mean_post_a = {t:Q(0) for t in mass}
    mean_max_post = {t:Q(0) for t in mass}
    conf = {t:Q(0) for t in mass}
    recover = {'A':Q(0),'B':Q(0)}
    post_by_k = {}
    information_terms = []
    for seq in product((0,1), repeat=n):
        k = sum(seq)
        la,lb,lc = (sequence_probability(p, seq) for p in (pa,pb,Q(1,2)))
        if la+lb == 0:
            raise ValueError('Zero prior predictive probability')
        a = la/(la+lb)
        b = 1-a
        if k in post_by_k:
            assert post_by_k[k] == a
        post_by_k[k] = a
        for t,lik in zip(('A','B','C'),(la,lb,lc)):
            mass[t][k] += lik
            mean_post_a[t] += lik*a
            mean_max_post[t] += lik*max(a,b)
            conf[t] += lik*(max(a,b)>=Q(19,20))
        score_a = Q(1) if la>lb else Q(0) if la<lb else Q(1,2)
        recover['A'] += la*score_a
        recover['B'] += lb*(1-score_a)
        # Direct joint-versus-product mutual information over model/sequence pairs.
        mixture = (la+lb)/2
        if la:
            information_terms.append(float(la/2)*math.log2(float(la/mixture)))
        if lb:
            information_terms.append(float(lb/2)*math.log2(float(lb/mixture)))
    assert all(sum(m)==1 for m in mass.values())
    return {'probability_A':pa,'probability_B':pb,'sequence_length':n,
            'count_masses':mass,'posterior_A_by_k':[post_by_k[k] for k in range(n+1)],
            'model_recovery':recover,'equal_prior_recovery':(recover['A']+recover['B'])/2,
            'EIG_bits':math.fsum(information_terms),'mean_posterior_A':mean_post_a,
            'mean_max_posterior':mean_max_post,'confidence_ge_0_95':conf}

def expect_reject(label, f):
    try:
        f()
    except (ValueError,TypeError,AssertionError):
        return {'test':label,'result':'PASS_REJECTED'}
    raise AssertionError('Invalid case accepted: '+label)

def metrics_from_hist(hist,post,truth):
    if len(hist)!=9 or any(type(v) is not int or v<0 for v in hist) or sum(hist)!=1000:
        raise ValueError('Invalid count histogram')
    conf = sum(h for h,a in zip(hist,post) if max(a,1-a)>=Q(19,20))/1000
    mean_a = float(sum((h*a for h,a in zip(hist,post)),Q(0))/1000)
    mean_max = float(sum((h*max(a,1-a) for h,a in zip(hist,post)),Q(0))/1000)
    recovery = None if truth=='C' else float(sum(h*(Q(1,2) if a==Q(1,2) else int((a>Q(1,2))==(truth=='A'))) for h,a in zip(hist,post)))/1000
    return {'recovery':recovery,'mean_posterior_A':mean_a,'mean_max_posterior':mean_max,'confidence_ge_0_95':conf}

def serial(value):
    if isinstance(value,Q): return {'rational':str(value),'float':float(value)}
    if isinstance(value,dict): return {str(k):serial(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [serial(v) for v in value]
    return value

def main():
    start=time.perf_counter()
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',default='/workspace/shared/frontier-neuroscience')
    parser.add_argument('--simulate',action='store_true')
    parser.add_argument('--design-order',choices=['diagnostic/ordinary','ordinary/diagnostic'],default='ordinary/diagnostic')
    parser.add_argument('--output',default=str(Path(__file__).with_name('oracle_results.json')))
    args=parser.parse_args()
    proto=Path(args.repo)/'problems/NEURO-001/experiments/synthetic_disagreement/protocol.json'
    assert hashlib.sha256(proto.read_bytes()).hexdigest()==PIN, 'Protocol pin mismatch'
    spec=json.loads(proto.read_text())
    assert tuple(map(Q,spec['selection_grid']))==GRID
    scores = [(x,enumerate_design(*probabilities(x),n=1)['EIG_bits']) for x in GRID]
    best=max(v for _,v in scores)
    selected=min(x for x,v in scores if best-v<=1e-14)
    designs={'diagnostic':enumerate_design(*probabilities(selected)),
             'ordinary':enumerate_design(*probabilities(Q(1,2)))}
    assert designs['ordinary']['equal_prior_recovery']==Q(1,2)
    assert abs(designs['ordinary']['EIG_bits'])<=1e-12
    assert designs['diagnostic']['equal_prior_recovery']-designs['ordinary']['equal_prior_recovery']>=Q(1,10)
    identical=[]
    for x in GRID:
        pa=probabilities(x)[0]
        item=enumerate_design(pa,pa)
        assert item['equal_prior_recovery']==Q(1,2) and item['EIG_bits']==0
        identical.append({'x':x,'EIG_bits':item['EIG_bits'],'recovery':item['equal_prior_recovery']})
    controls=[]
    for x in (Q(-5,4),Q(5,4),float('nan'),float('inf'),'1/2'):
        controls.append(expect_reject('invalid x '+repr(x),lambda x=x:probabilities(x)))
    for p in (Q(-1,100),Q(101,100),float('nan'),float('inf')):
        controls.append(expect_reject('invalid probability '+repr(p),lambda p=p:enumerate_design(p,Q(1,2))))
    for n in (0,-1,9,1.5,True):
        controls.append(expect_reject('invalid sequence length '+repr(n),lambda n=n:enumerate_design(Q(1,2),Q(1,2),n)))
    controls.append(expect_reject('invalid response',lambda:sequence_probability(Q(1,2),(0,2))))
    # The protocol does not freeze the design-index mapping explicitly. The mapping
    # is supplied explicitly after inspecting provenance for the comparison stage.
    simulations={}
    for ordering in ([tuple(args.design_order.split('/'))] if args.simulate else []):
        rows=[]
        for di,name in enumerate(ordering):
            exact=designs[name]
            for ti,t in enumerate(('A','B','C')):
                p=exact['probability_A'] if t=='A' else exact['probability_B'] if t=='B' else Q(1,2)
                for si in range(10):
                    seed=10000+100*di+10*ti+si
                    rng=random.Random(seed)
                    hist=[0]*9
                    for _ in range(1000):
                        k=0
                        for _ in range(8):
                            if rng.random()<float(p): k+=1
                        hist[k]+=1
                    rows.append({'design':name,'truth':t,'seed':seed,'histogram':hist,'metrics':metrics_from_hist(hist,exact['posterior_A_by_k'],t)})
        simulations['/'.join(ordering)]=rows
    output={'identity':'Independent verifier, separate session; protocol-first implementation before viewing author code/results',
            'scope':'Synthetic unit baseline only. Parent empirical NEURO-001 remains OPEN.',
            'protocol_sha256':PIN,'python':sys.version,'platform':platform.platform(),'selected_input':selected,
            'grid_scores':scores,'designs':designs,'identical_controls':identical,'invalid_controls':controls,
            'simulations_by_design_index_mapping':simulations,
            'limitations':['Protocol omits explicit design_index/truth_index label order; comparison run must supply an explicit design order matching author provenance.',
             'Protocol posterior mean metric does not name posterior_A vs maximum; both reported.',
             'No subject, session, stimulus-domain holdout or empirical causal inference.'],
            'elapsed_seconds':time.perf_counter()-start}
    Path(args.output).write_text(json.dumps(serial(output),indent=2)+'\n')
    print('PASS protocol hash '+PIN)
    print('Selected x:',selected,'single-response EIG bits:',best)
    for name,d in designs.items():
        print(name,'n=8 recovery:',d['equal_prior_recovery'],'=',float(d['equal_prior_recovery']),'EIG bits:',d['EIG_bits'])
        print(name,'C mean posterior A:',d['mean_posterior_A']['C'],'C mean maximum posterior:',float(d['mean_max_posterior']['C']),'C confidence >=0.95:',d['confidence_ge_0_95']['C'])
    print('PASS 9 identical-model cases;',len(controls),'invalid-input controls;',60 if args.simulate else 0,'independent seeded histograms')
    print('Output:',args.output,'elapsed_seconds:',output['elapsed_seconds'])

if __name__=='__main__': main()
