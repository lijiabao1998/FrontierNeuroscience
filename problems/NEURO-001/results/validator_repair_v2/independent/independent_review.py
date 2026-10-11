#!/usr/bin/env python3
"""One-shot independent, finite frozen-candidate audit. Never modifies target files.
Mathematical oracle: ordered responses, Fraction likelihoods, 70-digit Decimal
conditional entropy. No author mathematical function supplies oracle values.
"""
import copy
import datetime as dt
import hashlib
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys
import time
from decimal import Decimal, localcontext
from fractions import Fraction as F

sys.dont_write_bytecode = True
ROOT = Path('/workspace/shared/frontier-human-20261011/neuro_candidate')
OUT = Path(__file__).resolve().parent
EX = ROOT/'problems/NEURO-001/experiments/validator_repair_v2'
ORIGINAL = ROOT/'problems/NEURO-001/results/synthetic_disagreement/results.json'
REPLAY = ROOT/'problems/NEURO-001/results/validator_repair_v2/original_replay/problems/NEURO-001/results/synthetic_disagreement/results.json'
FREEZE = ROOT/'runs/20261011T041346153905Z-gpt-NEURO-001/code-freeze.json'
DEADLINE = dt.datetime.fromisoformat('2026-10-11T04:43:46.153905+00:00')
TOL = 1e-12
RESULT = {'verdict':'RUNNING', 'checks':[], 'calls':{'report':0,'parser':0,'expectation_seeded_pass':0,'guard_direct':0,'guard_internal':0},'scope':'Finite artifact validation only; no biological discovery or parent completion.', 'original_acceptance':'FAILED/INCOMPLETE'}

def now(): return dt.datetime.now(dt.timezone.utc)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(): (OUT/'results.json').write_text(json.dumps(RESULT, indent=2, allow_nan=False)+'\n')
def check(name, value, **detail):
    RESULT['checks'].append({'name':name,'pass':bool(value),**detail});save()
    if not value: raise AssertionError('Candidate or review failed: '+name)
def dump(p,x): Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def dec(x): return Decimal(x.numerator)/Decimal(x.denominator)
def entropy(p):
    with localcontext() as ctx:
        ctx.prec=70
        if p in (F(0),F(1)): return Decimal(0)
        p=dec(p); q=1-p
        return -(p*p.ln()+q*q.ln())/Decimal(2).ln()
def outcome_probability(p, bits):
    ans=F(1)
    for bit in bits: ans *= p if bit else 1-p
    return ans

def exact_oracle(a,b,t,truth,n=8):
    """Independent ordered-outcome enumeration, including exact posterior mean."""
    rec=F(0); high=F(0); mean=F(0); mass=[F(0)]*(n+1)
    posterior_by_count={}; score_by_count={}
    with localcontext() as ctx:
        ctx.prec=70
        conditional=Decimal(0)
        for bits in itertools.product((0,1),repeat=n):
            la=outcome_probability(a,bits); lb=outcome_probability(b,bits)
            lt=outcome_probability(t,bits)
            if la+lb==0: raise ValueError('Undefined posterior support')
            p=la/(la+lb); count=sum(bits)
            score=F(1) if la>lb else F(0) if la<lb else F(1,2)
            posterior_by_count[count]=p; score_by_count[count]=score
            mass[count]+=lt;mean+=lt*p
            if p>=F(19,20) or p<=F(1,20): high+=lt
            if truth=='A': rec+=lt*score
            elif truth=='B': rec+=lt*(1-score)
            conditional+=dec((la+lb)/2)*entropy(p)
        info=Decimal(1)-conditional
    assert sum(mass)==1
    result={'recovery_fraction':str(rec) if truth!='C' else None,
        'recovery':float(rec) if truth!='C' else None,
        'mean_posterior_A':float(mean),'high_confidence':float(high),
        'high_confidence_fraction':str(high),'binomial_mass':[str(x) for x in mass]}
    return result, {'mean_posterior_A_fraction':str(mean),'information_bits_decimal':str(info),
                    'posterior_by_count':[str(posterior_by_count[k]) for k in range(n+1)],
                    'map_score_A_by_count':[str(score_by_count[k]) for k in range(n+1)]}

def numerical_compare(got,expected,path='$',stats=None):
    if stats is None: stats={'float_comparisons':0,'max_absolute_difference':0.0}
    if isinstance(expected,dict):
        assert type(got) is dict and set(got)==set(expected), (path,'object fields')
        for k,v in expected.items(): numerical_compare(got[k],v,path+'.'+k,stats)
    elif isinstance(expected,list):
        assert type(got) is list and len(got)==len(expected),(path,'array shape')
        for i,(u,v) in enumerate(zip(got,expected)): numerical_compare(u,v,f'{path}[{i}]',stats)
    elif type(expected) is float:
        assert type(got) in (int,float) and math.isfinite(got),(path,'nonfinite/type')
        delta=abs(got-expected);assert delta<=TOL,(path,got,expected,delta)
        stats['float_comparisons']+=1; stats['max_absolute_difference']=max(stats['max_absolute_difference'],delta)
    else: assert type(got) is type(expected) and got==expected,(path,got,expected)
    return stats

def guard_fixtures():
    fixtures=[]
    values=[('tiny_negative',-F(1,10**40)),('tiny_above_one',F(1)+F(1,10**40)),('NaN',float('nan')),('positive_infinity',float('inf')),('negative_infinity',float('-inf')),('boolean_false',False)]
    for i in range(3):
        for name,value in values:
            args=[F(1,7),F(2,3),F(5,9),'C'];args[i]=value
            fixtures.append((f'guard_{i}_{name}',args,False))
    fixtures += [('guard_unknown_truth',[F(1,7),F(2,3),F(5,9),'D'],False),
                 ('guard_endpoint_unsupported_even_with_degenerate_truth',[F(1),F(0),F(0),'A'],False)]
    valid=[(F(1,7),F(2,3),F(5,9),'A'),(F(1,1000),F(999,1000),F(1,2),'C'),
           (F(1,2),F(1,3),F(0),'C'),(F(1,2),F(1,3),F(1),'B'),
           (F(0),F(1,2),F(1,5),'A'),(F(3,7),F(3,7),F(3,7),'A')]
    fixtures += [(f'guard_valid_heldout_{i}',list(args),True) for i,args in enumerate(valid)]
    return fixtures

def mutate_declared(original,item):
    v=copy.deepcopy(original);parent=v
    for k in item['path'][:-1]: parent=parent[k]
    k=item['path'][-1]; op=item['op']
    if op=='set': parent[k]=item['value']
    elif op=='add': parent[k]+=item['value']
    elif op=='nonfinite': parent[k]=float(item['value'])
    elif op=='delete': del parent[k]
    elif op=='reverse': parent[k]=parent[k][::-1]
    elif op=='copy_zero': parent[k]=copy.deepcopy(parent[0])
    elif op=='transfer':
        source=next(i for i,x in enumerate(parent[k]) if x>0)
        parent[k][source]-=1;parent[k][(source+1)%len(parent[k])]+=1
    else: raise ValueError(op)
    assert repr(v)!=repr(original),'mutation identity'
    return v

def report_call(v,name,report,accept=False,reason=''):
    RESULT['calls']['report']+=1
    assert RESULT['calls']['report']<=40
    accepted=False;err=None;ret=None
    try: ret=v.validate_report(report);accepted=True
    except (ValueError,TypeError,AssertionError,KeyError,IndexError,OverflowError) as e: err=type(e).__name__+': '+str(e)
    check(name,accepted==accept,expected='ACCEPT' if accept else 'REJECT',actual='ACCEPT' if accepted else 'REJECT',error=err,result=ret,reason=reason)
    return ret

def snapshot():
    paths=list(ROOT.rglob('*'))
    return {str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file() and '.git' not in p.relative_to(ROOT).parts}

def main():
    if (OUT/'results.json').exists(): raise RuntimeError('One-shot result already exists; no overwrite')
    start=now();t=time.monotonic();RESULT['started_at']=start.isoformat()
    if start>=DEADLINE:raise RuntimeError('Hard deadline expired')
    resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
    resource.setrlimit(resource.RLIMIT_CPU,(120,120))
    def expired(*_):raise TimeoutError('Review deadline reached')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,(DEADLINE-start).total_seconds())
    before=snapshot();dump(OUT/'source-hashes-before.json',before)
    save()
    try:
        protocol=json.loads((EX/'protocol.json').read_text()); freeze=json.loads(FREEZE.read_text())
        check('frozen_code_hashes',all(sha(ROOT/p)==h for p,h in freeze['sha256'].items()),hashes=freeze['sha256'])
        check('expected_protocol_identity',sha(EX/'protocol.json')=='97ccf1310b31de7cac5b253a58e0a267c7ec97d077fdb430d1f9488082311435')
        targets={'original_protocol_sha256':ROOT/'problems/NEURO-001/experiments/synthetic_disagreement/protocol.json','original_code_sha256':ROOT/'problems/NEURO-001/experiments/synthetic_disagreement/baseline.py','original_results_sha256':ORIGINAL}
        check('original_pinned_inputs',all(sha(p)==protocol['inputs'][k] for k,p in targets.items()))
        # Independent expected exact outputs persisted before importing validator.
        oracle={'method':'Ordered 256-response enumeration; rational likelihoods; 70-digit Decimal entropy; no author mathematics imported. Reviewer read code/results before independently authoring this oracle, so this is not blinded.','grid':[],'designs':[], 'guard_valid':{}}
        with localcontext() as ctx:
            ctx.prec=70
            for i in range(-4,5):
                x=F(i,4);a=(2+x)/4;b=(2+abs(x))/4
                eig=entropy((a+b)/2)-(entropy(a)+entropy(b))/2
                oracle['grid'].append({'x':str(x),'eig1':float(eig),'eig1_decimal':str(eig)})
        maximum=max(r['eig1'] for r in oracle['grid'])
        selected=next(F(r['x']) for r in oracle['grid'] if maximum-r['eig1']<=1e-14)
        oracle['selected_x']=str(selected)
        for name,x in [('ordinary',F(1,2)),('diagnostic',selected)]:
            a=(2+x)/4;b=(2+abs(x))/4
            d={'name':name,'x':str(x),'pA':str(a),'pB':str(b),'truths':{},'exact_details':{}}
            for truth,truthp in [('A',a),('B',b),('C',F(1,2))]:
                d['truths'][truth],d['exact_details'][truth]=exact_oracle(a,b,truthp,truth)
            d['eig8']=float(d['exact_details']['A']['information_bits_decimal'])
            d['equal_prior_recovery']=float((F(d['truths']['A']['recovery_fraction'])+F(d['truths']['B']['recovery_fraction']))/2)
            oracle['designs'].append(d)
        for name,args,accept in guard_fixtures():
            if accept: oracle['guard_valid'][name]=exact_oracle(*args)[0]
        dump(OUT/'independent-oracle.json',oracle)
        RESULT['oracle_sha256']=sha(OUT/'independent-oracle.json');save()
        spec=importlib.util.spec_from_file_location('frozen_validator_under_test',EX/'strict_validator.py')
        v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
        # The single remaining seeded pass uses the REAL unmodified validator.
        RESULT['calls']['expectation_seeded_pass']+=1
        frozen_expected=v.expected_payload(); RESULT['calls']['guard_internal']+=6
        check('exactly_one_seeded_pass',v.expected_payload.cache_info().misses==1)
        original=json.loads(ORIGINAL.read_text());replay=json.loads(REPLAY.read_text())
        expected={'protocol_sha256':protocol['inputs']['original_protocol_sha256'],'selected_x':oracle['selected_x'],'grid':[{k:r[k] for k in ('x','eig1')} for r in oracle['grid']],'configurations':60,'designs':[{k:d[k] for k in ('name','x','pA','pB','eig8','truths','equal_prior_recovery')} for d in oracle['designs']],'mc':[],'pooled_mc':[]}
        # Histogram bytes are tested against pinned evidence plus the real seeded
        # implementation. MC metrics are newly derived from counts and oracle.
        for di,d in enumerate(oracle['designs']):
            for ti,truth in enumerate(('A','B','C')):
                detail=d['exact_details'][truth];post=list(map(F,detail['posterior_by_count']));scores=list(map(F,detail['map_score_A_by_count']))
                for si in range(10):
                    index=di*30+ti*10+si;row=original['mc'][index];hist=row['histogram']
                    assert all(type(x) is int and x>=0 for x in hist) and len(hist)==9 and sum(hist)==1000
                    rec=None if truth=='C' else sum(F(c)*(s if truth=='A' else 1-s) for c,s in zip(hist,scores))/1000
                    conf=sum(F(c) for c,p in zip(hist,post) if p>=F(19,20) or p<=F(1,20))/1000
                    expected['mc'].append({'design':d['name'],'truth':truth,'seed':10000+100*di+10*ti+si,'histogram':hist,'recovery':float(rec) if rec is not None else None,'high_confidence':float(conf)})
                for metric in ('recovery','high_confidence'):
                    exact=d['truths'][truth][metric]
                    if exact is None:continue
                    rows=expected['mc'][-10:]
                    estimate=float(sum(F(str(r[metric])) for r in rows)/10)
                    expected['pooled_mc'].append({'design':d['name'],'truth':truth,'metric':metric,'estimate':estimate,'exact':exact,'abs_error':abs(estimate-exact)})
        stats=numerical_compare(frozen_expected,expected)
        check('candidate_vs_independent_exact_and_rederived_metrics',True,**stats)
        for name,payload in [('pinned_original',original),('fresh_author_replay',replay)]:
            stats=numerical_compare({k:payload[k] for k in expected},expected)
            check(name+'_vs_independent_oracle',True,**stats)
            report_call(v,name+'_accepted',payload,True)
        check('all_60_seeded_histograms_equal_pinned_original_and_replay',all(x['histogram']==y['histogram']==z['histogram'] for x,y,z in zip(frozen_expected['mc'],original['mc'],replay['mc'])))
        # Exercise every frozen declared mutation through the unmodified validator.
        for item in json.loads((EX/'mutations.json').read_text()):
            report_call(v,'declared_'+item['name'],mutate_declared(original,item))
        # Nine independently designed, pre-execution-frozen held-out reports.
        hidden=[]
        x=copy.deepcopy(original); x['pooled_mc'][5]['exact']+=0.05;x['pooled_mc'][5]['estimate']+=0.05
        hidden.append(('heldout_compensating_pooled_values',x,False,'Estimate and target shifted together; reported abs_error unchanged.'))
        x=copy.deepcopy(original);x['grid'][0]['x']='-4/4'
        hidden.append(('heldout_noncanonical_equivalent_rational',x,False,'Exact canonical rational-string contract.'))
        x=copy.deepcopy(original);x['mc'][59]['histogram'][4]=float(x['mc'][59]['histogram'][4])
        hidden.append(('heldout_histogram_integer_valued_float',x,False,'Numeric value unchanged; count type violated.'))
        x=copy.deepcopy(original);x['designs'][1]['equal_prior_recovery']+=0.01
        hidden.append(('heldout_equal_prior_summary_tamper',x,False,'Previously unmutated summary metric.'))
        x=copy.deepcopy(original);row=x['mc'][30];row['histogram'][0]-=1;row['histogram'][4]+=1
        post=list(map(F,oracle['designs'][1]['exact_details']['A']['posterior_by_count']));scores=list(map(F,oracle['designs'][1]['exact_details']['A']['map_score_A_by_count']))
        row['recovery']=float(sum(F(c)*s for c,s in zip(row['histogram'],scores))/1000)
        row['high_confidence']=float(sum(F(c) for c,p in zip(row['histogram'],post) if p>=F(19,20) or p<=F(1,20))/1000)
        for pooled in x['pooled_mc']:
            if pooled['design']=='diagnostic' and pooled['truth']=='A':
                pooled['estimate']=sum(r[pooled['metric']] for r in x['mc'] if r['design']=='diagnostic' and r['truth']=='A')/10
                pooled['abs_error']=abs(pooled['estimate']-pooled['exact'])
        hidden.append(('heldout_coherent_histogram_metric_rewrite',x,False,'Totals, per-seed metrics and affected pooled summaries recomputed coherently.'))
        x=copy.deepcopy(original);x['designs'][1]['truths']['C']['recovery']=0.5;x['designs'][1]['truths']['C']['recovery_fraction']='1/2'
        hidden.append(('heldout_outside_family_recovery_invention',x,False,'C is not an A/B candidate; recovery must remain null.'))
        x=copy.deepcopy(original);x['scientific_validation']='COMPLETE'
        hidden.append(('heldout_unrecognized_top_level_claim',x,False,'Unrecognized root field.'))
        overflow=copy.deepcopy(original);overflow['designs'][0]['eig8']='OVERFLOW_SENTINEL'
        overflow_text=json.dumps(overflow).replace('"OVERFLOW_SENTINEL"','1e400')
        RESULT['calls']['parser']+=1;overflow_parsed=v.strict_loads(overflow_text)
        check('parser_overflow_boundary_observed',math.isinf(overflow_parsed['designs'][0]['eig8']),classification='OUT_OF_SCOPE_PARSER_LIMITATION',detail='Valid JSON numeral 1e400 parses as infinity; report validation must reject it. Strict literal rejection does not ensure all parsed floats are finite.')
        hidden.append(('heldout_exponent_overflow_in_math',overflow_parsed,False,'Parser accepts overflow as inf; finite-math guard must reject.'))
        x=copy.deepcopy(original);x['independent_verification']='CLAIMED_COMPLETE';x['author_checks_passed']=True;x['controls']={'invented_claim':True};x['limits']='Unsupported biological assertion'
        hidden.append(('heldout_metadata_claim_spoof',x,True,'Known metadata deliberately excluded; returned NOT_VALIDATED and scientific_claim NONE are required.'))
        for name,payload,accept,reason in hidden:
            ret=report_call(v,name,payload,accept,reason)
            if name=='heldout_metadata_claim_spoof':check('metadata_spoof_not_endorsed',ret['metadata_claims']=='NOT_VALIDATED' and ret['scientific_claim']=='NONE' and ret['historical_acceptance']=='FAILED/INCOMPLETE')
        parser_cases=[('nested_nan','{"outer":{"x":NaN}}'),('metadata_positive_inf','{"runtime_seconds":Infinity}'),('array_negative_inf','{"x":[-Infinity]}'),('duplicate_root','{"x":0,"x":1}'),('duplicate_nested','{"outer":{"x":0,"x":1}}'),('escaped_duplicate','{"a":0,"\\u0061":1}')]
        for name,text in parser_cases:
            RESULT['calls']['parser']+=1
            try:v.strict_loads(text)
            except (ValueError,TypeError) as e:check('strict_json_'+name,True,error=str(e))
            else:check('strict_json_'+name,False)
        for name,args,accept in guard_fixtures():
            RESULT['calls']['guard_direct']+=1;err=None;got=None
            try:got=v.guarded_exact(*args);accepted=True
            except (ValueError,TypeError) as e:accepted=False;err=type(e).__name__+': '+str(e)
            check(name,accepted==accept,actual='ACCEPT' if accepted else 'REJECT',expected='ACCEPT' if accept else 'REJECT',error=err)
            if accept:
                stats=numerical_compare(got,oracle['guard_valid'][name]);check(name+'_independent_exact_match',True,**stats)
        cache=v.expected_payload.cache_info()
        check('no_second_seeded_pass',cache.misses==1,cache_hits=cache.hits,cache_misses=cache.misses)
        check('reviewer_call_budgets',RESULT['calls']['report']+RESULT['calls']['parser']+RESULT['calls']['expectation_seeded_pass']<=40 and RESULT['calls']['guard_direct']+RESULT['calls']['guard_internal']<=32)
        RESULT['seeded_replay']={'fresh_passes':1,'configurations':60,'sequences':60000,'draws':480000,'independence':'Actual frozen candidate RNG implementation replayed once; no second independently authored RNG replay. Exact math and count-derived metrics independently authored. Historical replay is separate evidence.'}
        RESULT['key_numbers']={'selected_x':oracle['selected_x'],'ordinary_recovery':oracle['designs'][0]['truths']['A']['recovery_fraction'],'diagnostic_recovery':oracle['designs'][1]['truths']['A']['recovery_fraction'],'diagnostic_EIG8_decimal':oracle['designs'][1]['exact_details']['A']['information_bits_decimal'],'outside_C_high_confidence':oracle['designs'][1]['truths']['C']['high_confidence_fraction']}
        RESULT['verdict']='PASS_FINITE_INDEPENDENT_REVIEW'
        RESULT['limitations']=['No empirical, neural, clinical, subject/session or unseen stimulus-domain data. Parent NEURO-001 remains OPEN; original acceptance stays FAILED/INCOMPLETE.','This is an independent implementation and adversarial audit in another agent session, not blinded review: frozen code and historical outputs were read before oracle authorship.','One actual-candidate seeded replay verifies 60 histograms; new independent exact arithmetic is distinct from the historical independently authored seeded oracle.','Finite fixtures do not establish universal security, denial-of-service resistance or all-model mathematical correctness.','Known metadata content is intentionally not validated; consumers must retain NOT_VALIDATED / NONE labels.','Strict parser rejects named nonfinite literals and duplicate keys but JSON exponent overflow may yield infinity; numerical report fields reject it. Parser-wide finite-float guarantee and metadata numeric safety are not established.']
    except BaseException as e:
        RESULT['verdict']='FAILED_OR_INCOMPLETE';RESULT['failure']=type(e).__name__+': '+str(e)
        raise
    finally:
        after=snapshot();dump(OUT/'source-hashes-after.json',after)
        changed=[p for p in before if after.get(p)!=before[p]]
        RESULT['source_integrity']={'files_pinned':len(before),'changed_existing_files':changed,'added_files':sorted(set(after)-set(before)),'all_existing_files_unchanged':not changed}
        if changed:RESULT['verdict']='FAILED_OR_INCOMPLETE'
        RESULT['completed_at']=now().isoformat();RESULT['elapsed_seconds']=time.monotonic()-t;RESULT['cpu_seconds']=time.process_time();RESULT['maxrss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        RESULT['completed_before_deadline']=now()<DEADLINE
        if not RESULT['completed_before_deadline']:RESULT['verdict']='FAILED_OR_INCOMPLETE'
        save();signal.setitimer(signal.ITIMER_REAL,0)
    print(json.dumps({k:RESULT[k] for k in ('verdict','calls','key_numbers','source_integrity','elapsed_seconds','cpu_seconds')},indent=2))

if __name__=='__main__':main()
