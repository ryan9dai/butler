import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from butler.app import create_app
from butler.models import Schedule
from butler.inference import MockInference

TEXT='Schedule Review from 2026-12-01T10:00:00+01:00 to 2026-12-01T11:00:00+01:00'
HEAD={'X-Butler-Client':'browser'}
@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path/'test.db',MockInference())) as c:
        yield c

def submit(c,key='a',text=TEXT):
    return c.post('/api/tasks',json={'key':key,'text':text},headers=HEAD)
def decide(c,t,approve=True):
    return c.post('/api/tasks/'+t['id']+'/decision',json={'approve':approve},headers=HEAD)

@pytest.mark.parametrize('start,end',[('2026-12-01T10:00:00','2026-12-01T11:00:00'),('2026-12-01T11:00:00Z','2026-12-01T10:00:00Z')])
def test_validation(start,end):
    with pytest.raises(ValidationError): Schedule(title='Test',start=start,end=end)

def test_approval_and_idempotency(client):
    t=submit(client).json()
    assert t['state']=='pending_approval'
    assert not client.get('/api/state').json()['calendar']
    assert submit(client).json()['id']==t['id']
    assert submit(client,text=TEXT+' changed').status_code==409
    assert decide(client,t).json()['state']=='completed'
    assert decide(client,t).json()['state']=='completed'
    assert len(client.get('/api/state').json()['calendar'])==1
    assert decide(client,t,False).status_code==409

def test_rejection(client):
    t=submit(client).json()
    assert decide(client,t,False).json()['state']=='rejected'
    assert decide(client,t).status_code==409
    assert not client.get('/api/state').json()['calendar']

def test_conflict_rechecked_at_approval(client):
    a=submit(client,'a').json();b=submit(client,'b').json()
    assert decide(client,a).status_code==200
    assert decide(client,b).status_code==409
    assert submit(client,'c').json()['state']=='conflict'
    adjacent=TEXT.replace('10:00:00','11:00:00').replace('11:00:00+01:00 to 2026-12-01T11:00:00','11:00:00+01:00 to 2026-12-01T12:00:00')
    assert submit(client,'d',adjacent).json()['state']=='pending_approval'

def test_invalid_extraction_is_audited(client):
    assert submit(client,text='sometime tomorrow').json()['state']=='failed'
    assert client.get('/api/state').json()['audit'][0]['event']=='extraction_failed'

def test_restart_persistence(tmp_path):
    db=tmp_path/'restart.db'
    with TestClient(create_app(db,MockInference())) as c:
        t=submit(c).json();decide(c,t)
        pending=submit(c,'pending',TEXT.replace('12-01','12-02')).json()
        with c.app.state.service.store.connect() as conn:
            conn.execute("INSERT INTO tasks(id,request_key,request,state) VALUES ('interrupted','x','test','extracting')")
    with TestClient(create_app(db,MockInference())) as c:
        state=c.get('/api/state').json()
        assert len(state['calendar'])==1
        assert c.app.state.service.task(pending['id'])['state']=='pending_approval'
        assert c.app.state.service.task('interrupted')['state']=='interrupted'
        assert decide(c,pending).status_code==200

def test_origin_and_unknown_task(client):
    assert client.post('/api/tasks',json={'key':'x','text':TEXT}).status_code==403
    assert client.post('/api/tasks',headers={**HEAD,'Origin':'http://evil.example'},json={'key':'x','text':TEXT}).status_code==403
    assert decide(client,{'id':'missing'}).status_code==404

def test_concurrent_approvals(client):
    a=submit(client,'a').json();b=submit(client,'b').json()
    with ThreadPoolExecutor(2) as pool:
        results=list(pool.map(lambda t:decide(client,t).status_code,[a,b]))
    assert sorted(results)==[200,409]
    assert len(client.get('/api/state').json()['calendar'])==1

def test_local_inference_contract(monkeypatch):
    import httpx
    from butler.inference import LocalInference
    real=httpx.AsyncClient
    calls=[]
    def handler(request):
        payload=json.loads(request.content)
        calls.append(payload)
        assert request.url.path=='/v1/chat/completions'
        assert payload['model']=='test-model'
        assert payload['response_format']=={'type':'json_object'}
        assert request.headers['X-LLM-Priority']=='10'
        if len(calls)==1:
            return httpx.Response(503)
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps({'title':'Test','start':'2026-12-01T10:00:00Z','end':'2026-12-01T11:00:00Z'})}}]})
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs:real(transport=httpx.MockTransport(handler),**kwargs))
    result=asyncio.run(LocalInference('http://localhost/v1','test-model','Europe/Monaco').extract('test'))
    assert result.title=='Test'
    assert len(calls)==2
