#!/usr/bin/env python3
"""One-shot frozen validation; stops and preserves report on candidate failure."""
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import platform
import resource
import shutil
import signal
import subprocess
import sys
import time
from fractions import Fraction as Q
sys.dont_write_bytecode = True
import strict_validator as validator

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ROUND = ROOT/'runs/20261011T041346153905Z-gpt-NEURO-001'
OUTPUT = ROOT/'problems/NEURO-001/results/validator_repair_v2'
ORIGINAL = ROOT/'problems/NEURO-001/experiments/synthetic_disagreement'
SAVED = ROOT/'problems/NEURO-001/results/synthetic_disagreement/results.json'
PROTOCOL = json.loads((HERE/'protocol.json').read_text())
RESULT = {'candidate':'validator-repair-v2','state':'RUNNING','checks':[],
    'legacy_controls':[],'parent_problem':'OPEN','new_discovery':False,
    'original_acceptance':'FAILED/INCOMPLETE'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save():
    (OUTPUT/'results.json').write_text(json.dumps(RESULT,indent=2,allow_nan=False)+'\n')


def check(name, call, reject=False):
    outcome = {'name':name,'expected':'REJECT' if reject else 'ACCEPT'}
    try:
        call()
    except (ValueError, TypeError, AssertionError, KeyError, IndexError) as error:
        outcome.update(actual='REJECT',error=type(error).__name__+': '+str(error))
    else:
        outcome['actual'] = 'ACCEPT'
    outcome['pass'] = outcome['actual'] == outcome['expected']
    RESULT['checks'].append(outcome)
    save()
    if not outcome['pass']:
        raise RuntimeError('Frozen candidate failed: '+name)


def mutation(original, item):
    data = copy.deepcopy(original)
    path = item['path'];obj=data
    for key in path[:-1]: obj=obj[key]
    key=path[-1];op=item['op']
    if op == 'set': obj[key]=item['value']
    elif op == 'add': obj[key]+=item['value']
    elif op == 'nonfinite': obj[key]=float(item['value'])
    elif op == 'delete': del obj[key]
    elif op == 'reverse': obj[key].reverse()
    elif op == 'copy_zero': obj[key]=copy.deepcopy(obj[0])
    elif op == 'transfer':
        hist=obj[key];source=next(i for i,v in enumerate(hist) if v>0)
        hist[source]-=1;hist[(source+1)%len(hist)]+=1
    else: raise ValueError('Unknown frozen mutation')
    return data


def import_original():
    spec = importlib.util.spec_from_file_location('original_neuro_baseline',ORIGINAL/'baseline.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def pinned_source_checks():
    expected = PROTOCOL['inputs']
    actual = {'original_protocol_sha256':sha(ORIGINAL/'protocol.json'),
              'original_code_sha256':sha(ORIGINAL/'baseline.py'),
              'original_results_sha256':sha(SAVED)}
    if actual != expected: raise RuntimeError('Original source integrity failure')
    return actual


def main():
    # No resume/overwrite hides a previous attempt.
    OUTPUT.mkdir(parents=True,exist_ok=False)
    started=dt.datetime.now(dt.timezone.utc);t0=time.monotonic()
    RESULT['started_at']=started.isoformat()
    save()
    try:
        deadline=dt.datetime.fromisoformat(PROTOCOL['budget']['hard_deadline'])
        if started>=deadline: raise RuntimeError('Full-round hard deadline expired')
        round_record=json.loads((ROUND/'round.json').read_text())
        if round_record['state']!='ADMITTED' or not round_record.get('public_claim_url'):
            raise RuntimeError('Admission and verified public claim required')
        def timed_out(signum, frame):
            raise TimeoutError('Full-round hard deadline reached')
        signal.signal(signal.SIGALRM,timed_out)
        signal.setitimer(signal.ITIMER_REAL,(deadline-started).total_seconds())
        resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
        resource.setrlimit(resource.RLIMIT_CPU,(1800,1800))
        RESULT['started_at']=started.isoformat()
        RESULT['environment']={'python':sys.version,'platform':platform.platform()}
        RESULT['pins_before']=pinned_source_checks()
        freeze=json.loads((ROUND/'code-freeze.json').read_text())
        for path,digest in freeze['sha256'].items():
            if sha(ROOT/path)!=digest: raise RuntimeError('Code-freeze mismatch: '+path)
        RESULT['code_freeze']=freeze
        save()
        # Known input rejection and boundary controls before report replay.
        for argument in range(3):
            for label,bad in [('negative',Q(-1,4)),('above_one',Q(5,4)),
                              ('nan',float('nan')),('positive_inf',float('inf')),
                              ('negative_inf',float('-inf')),('boolean',True)]:
                args=[Q(1,4),Q(3,4),Q(1,2),'C'];args[argument]=bad
                check(f'probability_arg{argument}_{label}',lambda args=args:validator.guarded_exact(*args),True)
        check('unknown_truth',lambda:validator.guarded_exact(Q(1,4),Q(3,4),Q(1,2),'X'),True)
        check('undefined_posterior_endpoints',lambda:validator.guarded_exact(Q(0),Q(1),Q(1,2),'C'),True)
        for index,(a,b,t,truth) in enumerate([(Q(1,4),Q(3,4),Q(1,4),'A'),
                (Q(1,4),Q(3,4),Q(3,4),'B'),(Q(1,4),Q(3,4),Q(1,2),'C'),
                (Q(1,2),Q(1,2),Q(0),'C'),(Q(1,2),Q(1,2),Q(1),'C')]):
            check('valid_probability_fixture_'+str(index),lambda a=a,b=b,t=t,truth=truth:validator.guarded_exact(a,b,t,truth))
        for label,text in [('nan','{"x":NaN}'),('inf','{"x":Infinity}'),
                ('negative_inf','{"x":-Infinity}'),('duplicate','{"x":1,"x":2}')]:
            check('strict_json_'+label,lambda text=text:validator.strict_loads(text),True)
        original=validator.strict_loads(SAVED.read_text())
        check('pinned_original_payload',lambda:validator.validate_report(original))
        mutations=json.loads((HERE/'mutations.json').read_text())
        for item in mutations:
            broken = mutation(original,item)
            if same_typed(broken, original):
                raise RuntimeError('Mutation did not alter fixture: '+item['name'])
            check('report_'+item['name'],lambda broken=broken:validator.validate_report(broken),True)
        old=import_original()
        for item in mutations:
            if not item.get('legacy'): continue
            broken = mutation(original,item)
            if same_typed(broken, original): raise RuntimeError('Legacy mutation did not alter fixture')
            try:old.validate_report(broken);rejected=False
            except (ValueError,TypeError,AssertionError):rejected=True
            RESULT['legacy_controls'].append({'name':item['name'],'rejected':rejected})
        try:old.exact(Q(1,4),Q(3,4),Q(2),'C');rejected=False
        except (ValueError,TypeError,AssertionError):rejected=True
        RESULT['legacy_controls'].append({'name':'invalid_truth_probability','rejected':rejected})
        save()
        # Replay original code only in a new evidence-copy directory.
        temp=OUTPUT/'original_replay';target=temp/'problems/NEURO-001/experiments/synthetic_disagreement'
        target.mkdir(parents=True)
        for name in ('baseline.py','protocol.json'):shutil.copy2(ORIGINAL/name,target/name)
        remaining=(deadline-dt.datetime.now(dt.timezone.utc)).total_seconds()
        if remaining<=0:raise RuntimeError('Full-round hard deadline expired')
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
        run=subprocess.run([sys.executable,str(target/'baseline.py')],capture_output=True,
                           timeout=min(remaining,1800),env=env)
        (OUTPUT/'baseline.stdout.txt').write_bytes(run.stdout)
        (OUTPUT/'baseline.stderr.txt').write_bytes(run.stderr)
        RESULT['baseline_exit_code']=run.returncode
        if run.returncode:raise RuntimeError('Original replay failed')
        replay=validator.strict_loads((temp/'problems/NEURO-001/results/synthetic_disagreement/results.json').read_text())
        a,b=copy.deepcopy(original),copy.deepcopy(replay)
        for data in (a,b):
            del data['runtime_seconds'];del data['environment']['python'];del data['environment']['platform']
        check('all_nondynamic_original_fields_exact',lambda:require_equal(a,b))
        check('fresh_replay_payload',lambda:validator.validate_report(replay))
        RESULT['pins_after']=pinned_source_checks()
        RESULT['state']='PASS_FINITE_AUTHOR_TESTS'
        RESULT['independent_validation']='PENDING_CURRENT_REVIEW'
        RESULT['elapsed_seconds']=time.monotonic()-t0
        RESULT['cpu_seconds']=time.process_time()
        RESULT['maxrss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        RESULT['completed_at']=dt.datetime.now(dt.timezone.utc).isoformat()
        if dt.datetime.now(dt.timezone.utc)>deadline:raise RuntimeError('Hard deadline exceeded')
    except BaseException as error:
        RESULT['state']='FAILED_OR_INCOMPLETE';RESULT['failure']=type(error).__name__+': '+str(error);save();raise
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        RESULT['pins_after_observed']={}
        for name,path in [('original_protocol_sha256',ORIGINAL/'protocol.json'),('original_code_sha256',ORIGINAL/'baseline.py'),('original_results_sha256',SAVED)]:
            try: RESULT['pins_after_observed'][name]=sha(path)
            except OSError as error: RESULT['pins_after_observed'][name]='UNREADABLE: '+str(error)
        RESULT['original_sources_unchanged']=RESULT['pins_after_observed']==PROTOCOL['inputs']
        RESULT['elapsed_seconds']=time.monotonic()-t0
        RESULT['cpu_seconds_parent']=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime
        RESULT['cpu_seconds_children']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime+resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime
        RESULT['maxrss_children_kib']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        save()
    save();print(json.dumps({k:RESULT[k] for k in ('state','elapsed_seconds','cpu_seconds','maxrss_kib','original_acceptance','independent_validation')},indent=2))


def same_typed(a,b):
    if type(a) is not type(b): return False
    if isinstance(a,dict):
        return set(a)==set(b) and all(same_typed(a[k],b[k]) for k in a)
    if isinstance(a,list):
        return len(a)==len(b) and all(same_typed(x,y) for x,y in zip(a,b))
    return a==b


def require_equal(a,b):
    if not same_typed(a,b):raise ValueError('Exact typed baseline replay differs outside frozen exclusions')


if __name__=='__main__': main()
