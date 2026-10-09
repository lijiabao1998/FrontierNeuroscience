#!/usr/bin/env python3
"""Purpose-built Bernoulli unit benchmark. No neural or clinical measurements."""
import hashlib,json,math,platform,random,sys,time
from fractions import Fraction as F
from pathlib import Path
from math import comb

def prob(model,x):
    if not -1<=x<=1: raise ValueError('outside frozen domain')
    if model=='A': return (2+x)/4
    if model=='B': return (2+abs(x))/4
    if model=='C': return F(1,2)
    raise ValueError('unknown model')
def entropy(p):
    if not 0<=p<=1: raise ValueError('invalid probability')
    return -sum(float(q)*math.log2(float(q)) for q in (p,1-p) if q)
def eig_one(a,b):return entropy((a+b)/2)-(entropy(a)+entropy(b))/2
def mass(p,k,n=8):return comb(n,k)*p**k*(1-p)**(n-k)
def row(a,b,truth,k):
    la=mass(a,k);lb=mass(b,k);post=la/(la+lb)
    score=F(1,2) if la==lb else F(int((la>lb)==(truth=='A')))
    return post,score

def exact(a,b,t,truth):
    probs=[mass(t,k) for k in range(9)];assert sum(probs)==1
    post=[row(a,b,truth,k)[0] for k in range(9)]
    score=[row(a,b,truth,k)[1] for k in range(9)]
    recovery=sum(p*s for p,s in zip(probs,score)) if truth in ('A','B') else None
    confidence=sum(p for p,q in zip(probs,post) if max(q,1-q)>=F(95,100))
    return {'recovery_fraction':str(recovery) if recovery is not None else None,'recovery':float(recovery) if recovery is not None else None,'mean_posterior_A':float(sum(p*q for p,q in zip(probs,post))),'high_confidence':float(confidence),'high_confidence_fraction':str(confidence),'binomial_mass':[str(p) for p in probs]}
def eig_eight(a,b):
    return 1-sum(float((mass(a,k)+mass(b,k))/2)*entropy(row(a,b,'A',k)[0]) for k in range(9))
def validate_report(r):
    if r['configurations']!=60 or len(r['mc'])!=60:raise ValueError('configuration mismatch')
    for v in r['mc']:
        if len(v['histogram'])!=9 or sum(v['histogram'])!=1000 or any(type(k)!=int or k<0 for k in v['histogram']):raise ValueError('invalid histogram')
    if abs(r['designs'][0]['equal_prior_recovery']-.5)>1e-12:raise ValueError('ordinary control failed')
    if abs(r['designs'][0]['eig8'])>1e-12:raise ValueError('ordinary EIG failed')

def main():
    began=time.monotonic();grid=[F(i,4) for i in range(-4,5)]
    scores=[eig_one(prob('A',x),prob('B',x)) for x in grid]
    chosen=next(x for x,v in zip(grid,scores) if max(scores)-v<=1e-14)
    checks={}
    checks['positive_domain_identical']=all(prob('A',x)==prob('B',x) for x in grid if x>=0)
    checks['identical_model_null']=all(abs(eig_one(prob('A',x),prob('A',x)))<1e-12 and exact(prob('A',x),prob('A',x),prob('A',x),'A')['recovery']==.5 for x in grid)
    for name,call in [('invalid_x',lambda:prob('A',F(2))),('invalid_model',lambda:prob('X',F(0))),('invalid_probability',lambda:entropy(F(2)))]:
        try:call();checks[name]=False
        except ValueError:checks[name]=True
    assert all(checks.values()),checks
    out={'protocol_sha256':hashlib.sha256(Path(__file__).with_name('protocol.json').read_bytes()).hexdigest(),'selected_x':str(chosen),'grid':[{'x':str(x),'eig1':v} for x,v in zip(grid,scores)],'configurations':60,'designs':[],'mc':[],'controls':checks,'limits':'Synthetic prescribed-model unit benchmark; C is outside candidate family. No empirical neural mechanism, clinical utility or generalization claim.'}
    for di,(name,x) in enumerate([('ordinary',F(1,2)),('diagnostic',chosen)]):
        a,b=prob('A',x),prob('B',x)
        d={'name':name,'x':str(x),'pA':str(a),'pB':str(b),'eig8':eig_eight(a,b),'truths':{}}
        for ti,truth in enumerate(('A','B','C')):
            t=prob(truth,x);d['truths'][truth]=exact(a,b,t,truth)
            for si in range(10):
                seed=10000+100*di+10*ti+si;rng=random.Random(seed);hist=[0]*9
                for _ in range(1000):hist[sum(rng.random()<float(t) for _ in range(8))]+=1
                rec=sum(n*float(row(a,b,truth,k)[1]) for k,n in enumerate(hist))/1000 if truth!='C' else None
                high=sum(n for k,n in enumerate(hist) if max(row(a,b,truth,k)[0],1-row(a,b,truth,k)[0])>=F(95,100))/1000
                out['mc'].append({'design':name,'truth':truth,'seed':seed,'histogram':hist,'recovery':rec,'high_confidence':high})
        d['equal_prior_recovery']=(d['truths']['A']['recovery']+d['truths']['B']['recovery'])/2;out['designs'].append(d)
    checks['diagnostic_gain_at_least_0_1']=out['designs'][1]['equal_prior_recovery']-out['designs'][0]['equal_prior_recovery']>=.1
    pooled=[]
    for d in out['designs']:
        for truth,e in d['truths'].items():
            rows=[v for v in out['mc'] if v['design']==d['name'] and v['truth']==truth]
            for metric in ('recovery','high_confidence'):
                if e[metric] is None:continue
                estimate=sum(v[metric] for v in rows)/10;error=abs(estimate-e[metric]);pooled.append({'design':d['name'],'truth':truth,'metric':metric,'estimate':estimate,'exact':e[metric],'abs_error':error})
    out['pooled_mc']=pooled;checks['mc_consistency']=all(p['abs_error']<=.025 for p in pooled)
    validate_report(out)
    bad=json.loads(json.dumps(out));bad['mc'][0]['histogram'][0]+=1
    try:validate_report(bad);checks['tampered_histogram_rejected']=False
    except ValueError:checks['tampered_histogram_rejected']=True
    out['author_checks_passed']=all(checks.values());out['independent_verification']='PENDING';out['runtime_seconds']=time.monotonic()-began;out['environment']={'python':sys.version,'platform':platform.platform()}
    dest=Path(__file__).parents[2]/'results/synthetic_disagreement';dest.mkdir(parents=True,exist_ok=True);(dest/'results.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'selected_x':str(chosen),'designs':out['designs'],'controls':checks,'runtime_seconds':out['runtime_seconds'],'independent_verification':'PENDING'},indent=2));return 0 if out['author_checks_passed'] else 1
if __name__=='__main__':sys.exit(main())
