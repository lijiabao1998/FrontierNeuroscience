#!/usr/bin/env python3
"""Compare independently generated oracle outputs with frozen author artifacts.
The author's validation helper is loaded only for adversarial control auditing;
it is not used to derive the oracle or to judge numerical agreement.
"""
from fractions import Fraction as Q
from pathlib import Path
import argparse, copy, hashlib, json, math, runpy, sys

BASELINE_SHA='01e492d41322b4983526635012613dc039d402f005b704eefaf5a03ecc1e02aa'
RESULT_SHA='4cf9f92ad5d522fc9319d37aad7c345f793416ce7089c9f03073777547cb042e'
TOL=1e-12

def rat(x): return Q(x['rational'])
def fl(x): return x['float']
def near(a,b,where):
    if not isinstance(a,(float,int)) or isinstance(a,bool) or not math.isfinite(a) or abs(a-b)>TOL:
        raise ValueError(f'{where}: {a!r} != {b!r}')
def equal(a,b,where):
    if a!=b: raise ValueError(f'{where}: {a!r} != {b!r}')

def compare(r,o):
    equal(r['protocol_sha256'],o['protocol_sha256'],'protocol hash')
    equal(Q(r['selected_x']),rat(o['selected_input']),'selected input')
    equal(len(r['grid']),9,'grid length')
    errors=[]
    for i,(ar,(x,sc)) in enumerate(zip(r['grid'],o['grid_scores'])):
        equal(Q(ar['x']),rat(x),f'grid[{i}].x')
        near(ar['eig1'],sc,f'grid[{i}].EIG')
        errors.append(abs(ar['eig1']-sc))
    equal([d['name'] for d in r['designs']],['ordinary','diagnostic'],'design order')
    for a in r['designs']:
        name=a['name'];d=o['designs'][name]
        equal(Q(a['x']),Q(1,2) if name=='ordinary' else rat(o['selected_input']),name+'.x')
        equal(Q(a['pA']),rat(d['probability_A']),name+'.pA')
        equal(Q(a['pB']),rat(d['probability_B']),name+'.pB')
        near(a['eig8'],d['EIG_bits'],name+'.EIG8');errors.append(abs(a['eig8']-d['EIG_bits']))
        near(a['equal_prior_recovery'],fl(d['equal_prior_recovery']),name+'.recovery')
        equal(set(a['truths']),{'A','B','C'},name+'.truths')
        for t,m in a['truths'].items():
            exp=d['count_masses'][t]
            equal([Q(v) for v in m['binomial_mass']],[rat(v) for v in exp],name+'/'+t+'/mass')
            near(m['mean_posterior_A'],fl(d['mean_posterior_A'][t]),name+'/'+t+'/mean')
            near(m['high_confidence'],fl(d['confidence_ge_0_95'][t]),name+'/'+t+'/confidence')
            equal(Q(m['high_confidence_fraction']),rat(d['confidence_ge_0_95'][t]),name+'/'+t+'/confidence fraction')
            if t=='C':
                equal(m['recovery'],None,'C recovery');equal(m['recovery_fraction'],None,'C recovery fraction')
            else:
                near(m['recovery'],fl(d['model_recovery'][t]),name+'/'+t+'/recovery')
                equal(Q(m['recovery_fraction']),rat(d['model_recovery'][t]),name+'/'+t+'/recovery fraction')
    own=o['simulations_by_design_index_mapping']['ordinary/diagnostic']
    equal(r['configurations'],60,'configuration count');equal(len(r['mc']),60,'MC length')
    for i,(ar,ind) in enumerate(zip(r['mc'],own)):
        for field in ('design','truth','seed','histogram'): equal(ar[field],ind[field],f'MC[{i}].{field}')
        if ar['truth']=='C': equal(ar['recovery'],None,f'MC[{i}].recovery')
        else: near(ar['recovery'],ind['metrics']['recovery'],f'MC[{i}].recovery')
        near(ar['high_confidence'],ind['metrics']['confidence_ge_0_95'],f'MC[{i}].confidence')
    equal(len(r['pooled_mc']),10,'pooled metric count')
    pooled=[]
    for name in ('ordinary','diagnostic'):
        for t in ('A','B','C'):
            ownrows=[q for q in own if q['design']==name and q['truth']==t]
            for metric in ('recovery','high_confidence'):
                if t=='C' and metric=='recovery': continue
                of='recovery' if metric=='recovery' else 'confidence_ge_0_95'
                target=fl(o['designs'][name]['model_recovery'][t]) if metric=='recovery' else fl(o['designs'][name]['confidence_ge_0_95'][t])
                estimate=math.fsum(q['metrics'][of] for q in ownrows)/10
                error=abs(estimate-target)
                if error>0.025: raise ValueError('Pooled MC exceeds frozen threshold')
                matches=[v for v in r['pooled_mc'] if (v['design'],v['truth'],v['metric'])==(name,t,metric)]
                equal(len(matches),1,'unique pooled metric')
                for key,val in [('estimate',estimate),('exact',target),('abs_error',error)]: near(matches[0][key],val,'pooled.'+key)
                pooled.append({'design':name,'truth':t,'metric':metric,'estimate':estimate,'exact':target,'absolute_error':error})
    equal(r['author_checks_passed'],True,'author control flag')
    if not all(v is True for v in r['controls'].values()): raise ValueError('Author reports failed control')
    return {'max_entropy_absolute_difference':max(errors),'histograms_exactly_equal':60,'pooled':pooled,'max_pooled_absolute_error':max(v['absolute_error'] for v in pooled)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',default='/workspace/shared/frontier-neuroscience');p.add_argument('--out',default=str(Path(__file__).with_name('comparison.json')));args=p.parse_args()
    repo=Path(args.repo);base=repo/'problems/NEURO-001/experiments/synthetic_disagreement/baseline.py';res=repo/'problems/NEURO-001/results/synthetic_disagreement/results.json'
    hashes={'baseline.py':hashlib.sha256(base.read_bytes()).hexdigest(),'results.json':hashlib.sha256(res.read_bytes()).hexdigest()}
    equal(hashes['baseline.py'],BASELINE_SHA,'baseline pin');equal(hashes['results.json'],RESULT_SHA,'result pin')
    original=json.loads(res.read_text());own=json.loads(Path(__file__).with_name('oracle_results.json').read_text())
    agreement=compare(original,own)
    print('PASS independent sequence-enumeration arithmetic and all 60 seeded histograms')
    print('Maximum entropy absolute discrepancy:',agreement['max_entropy_absolute_difference'])
    print('Maximum pooled MC absolute discrepancy:',agreement['max_pooled_absolute_error'])
    # No baseline main call and no writes in the author repository.
    sys.dont_write_bytecode=True
    namespace=runpy.run_path(str(base),run_name='author_control_audit_only')
    validator=namespace['validate_report']
    cases=[]
    def case(name,mutate):
        bad=copy.deepcopy(original);mutate(bad)
        try: validator(bad);author='ACCEPTED'
        except Exception as e: author='REJECTED';author_error=type(e).__name__+': '+str(e)
        try: compare(bad,own);ours='ACCEPTED'
        except Exception as e: ours='REJECTED';our_error=type(e).__name__+': '+str(e)
        cases.append({'case':name,'author_validator':author,'independent_verifier':ours,
                      'author_error':locals().get('author_error'),'independent_error':locals().get('our_error')})
        print('CONTROL',name,'author='+author,'independent='+ours)
    case('histogram_total_plus_one',lambda r:r['mc'][0]['histogram'].__setitem__(0,r['mc'][0]['histogram'][0]+1))
    def balanced(r): r['mc'][0]['histogram'][0]+=1;r['mc'][0]['histogram'][1]-=1
    case('histogram_redistribution_total_preserved',balanced)
    case('diagnostic_EIG_plus_0_125',lambda r:r['designs'][1].__setitem__('eig8',r['designs'][1]['eig8']+0.125))
    case('diagnostic_C_confidence_set_zero',lambda r:r['designs'][1]['truths']['C'].__setitem__('high_confidence',0))
    case('ordinary_EIG_NaN',lambda r:r['designs'][0].__setitem__('eig8',float('nan')))
    case('selected_input_changed',lambda r:r.__setitem__('selected_x','1'))
    case('duplicated_seed',lambda r:r['mc'][1].__setitem__('seed',r['mc'][0]['seed']))
    assert all(c['independent_verifier']=='REJECTED' for c in cases)
    pure=[]
    for name,fn in [('invalid_x',lambda:namespace['prob']('A',Q(2))),('invalid_model',lambda:namespace['prob']('X',Q(0))),('entropy_invalid_probability',lambda:namespace['entropy'](Q(2))),('exact_invalid_truth_probability',lambda:namespace['exact'](Q(1,4),Q(3,4),Q(2),'A'))]:
        try:
            val=fn();item={'case':name,'author_result':'ACCEPTED','returned':val}
        except Exception as e:item={'case':name,'author_result':'REJECTED','error':type(e).__name__+': '+str(e)}
        pure.append(item);print('INPUT CONTROL',name,item['author_result'])
    rounddir=repo/'runs/20261009T222712980221Z-gpt-NEURO-001'
    stdout=json.loads((rounddir/'baseline.stdout').read_text())
    for key in ('selected_x','designs','controls'): equal(stdout[key],original[key],'stdout.'+key)
    equal((rounddir/'baseline.exitcode').read_text().strip(),'0','author exit code')
    equal((rounddir/'baseline.stderr').read_text(),'','author stderr')
    # Assert we have left the immutable comparison targets intact.
    equal(hashlib.sha256(base.read_bytes()).hexdigest(),BASELINE_SHA,'baseline unchanged')
    equal(hashlib.sha256(res.read_bytes()).hexdigest(),RESULT_SHA,'results unchanged')
    result={'numeric_verdict':'PASS_FOR_FROZEN_SYNTHETIC_INSTANCE','control_adequacy':'LIMITED: author validator rejects malformed histogram but accepts semantic tampering and NaN; independent verifier rejects all seven injected corruptions.',
            'parent_problem_status':'OPEN','artifact_hashes':hashes,'agreement':agreement,'tampered_controls':cases,'author_input_controls':pure,
            'scope':'256 ordered sequences per design, exact rational masses/posteriors; logarithms floating point <=1e-12. No biological evidence or novelty.',
            'independence':'Oracle implemented and exact outputs saved before author source/results read; author source subsequently read to identify index order and audit controls. Author functions never used for oracle computation.',
            'protocol_ambiguities':['Design index label order unspecified; author source resolves ordinary then diagnostic.','Truth index label order implicit; author source resolves A/B/C.','Posterior mean referent unspecified; author implementation resolves mean P(A|Y).'],
            'raw_stdout_and_exitcode_match':True}
    Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print('PASS author stdout, stderr, exit code and immutable artifact hashes')
    print('NUMERIC VERDICT:',result['numeric_verdict']);print('CONTROL ADEQUACY:',result['control_adequacy'])
    print('Output:',args.out)
if __name__=='__main__':main()
