#!/usr/bin/env python3
"""Automated re-tests for the Agent Economy Index. Appends one dated JSON line per check to observations/<id>.jsonl.
Only public, unauthenticated, read-only endpoints; polite (one request per platform per run)."""
import json, urllib.request, datetime, os, re
OUT = os.path.join(os.path.dirname(__file__), '..', 'observations')
UA = {'User-Agent': 'AgentEconomyIndex/0.1 (+https://github.com/agentoprimus/agent-economy-index)'}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r: return json.load(r)
def superteam():
    L = get('https://superteam.fun/api/listings?take=100'); a = [x for x in L if x.get('agentAccess') != 'HUMAN_ONLY']
    return {'openListings': len(L), 'agentEligible': len(a), 'agentEligibleUsd': sum(x.get('rewardAmount') or 0 for x in a if (x.get('token') or '').upper() in ('USDC','USDT','USD')),
            'agentListings': [{'title': x['title'][:80], 'reward': x.get('rewardAmount'), 'token': x.get('token'), 'submissions': (x.get('_count') or {}).get('Submission')} for x in a]}
def taskmarket():
    T = get('https://taskmarket.dev/api/tasks')['tasks']; o = [t for t in T if t.get('status') == 'open']
    rw = [int(t.get('reward') or 0) / 1e6 for t in T]
    return {'tasksListed': len(T), 'open': len(o), 'rewardMinUsd': min(rw) if rw else None, 'rewardMaxUsd': max(rw) if rw else None,
            'chainIds': sorted({t.get('chainId') for t in T})}
def openrouter_free():
    M = get('https://openrouter.ai/api/v1/models')['data']; f = [m['id'] for m in M if m['id'].endswith(':free')]
    return {'models': len(M), 'freeModels': len(f), 'free': f}
def apify_new_creator_visibility():
    d = get('https://api.apify.com/v2/store?username=agentoprimus&limit=10')['data']
    return {'storeTotalForUser': d.get('total'), 'itemsReturned': len(d.get('items', [])), 'note': 'own account; tests whether new creators are listed in Store search'}
CHECKS = {'superteam-earn': superteam, 'taskmarket': taskmarket, 'openrouter': openrouter_free, 'apify-store': apify_new_creator_visibility}
if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True); now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ')
    for pid, fn in CHECKS.items():
        try: obs = {'at': now, 'ok': True, **fn()}
        except Exception as e: obs = {'at': now, 'ok': False, 'error': str(e)[:200]}
        with open(os.path.join(OUT, pid + '.jsonl'), 'a') as f: f.write(json.dumps(obs) + '\n')
        print(pid, {k: v for k, v in obs.items() if k not in ('free', 'agentListings')})
