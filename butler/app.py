import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request as HTTPRequest
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .storage import Store
from .service import Service, Conflict
from .models import Request, Decision
from .inference import LocalInference, MockInference

ROOT = Path(__file__).resolve().parent.parent

def create_app(db=None, inference=None):
    mode = os.getenv('BUTLER_INFERENCE','openai')
    backend = inference or (MockInference() if mode == 'mock' else LocalInference(
        os.getenv('BUTLER_INFERENCE_URL','http://127.0.0.1:18081/v1'),
        os.getenv('BUTLER_MODEL','gemma26b'),os.getenv('BUTLER_TIMEZONE','Europe/Monaco')))
    store = Store(db or os.getenv('BUTLER_DB','data/butler.db'))
    service = Service(store,backend)
    @asynccontextmanager
    async def lifespan(app):
        service.recover()
        yield
    app = FastAPI(title='Butler',lifespan=lifespan)
    app.state.service = service
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=os.getenv('BUTLER_ALLOWED_HOSTS','localhost,127.0.0.1,100.64.0.7,testserver').split(','))

    @app.middleware('http')
    async def guard(request: HTTPRequest, call_next):
        if request.method not in ('GET','HEAD','OPTIONS'):
            if request.headers.get('x-butler-client') != 'browser' or request.headers.get('sec-fetch-site') == 'cross-site':
                return JSONResponse({'detail':'Same-origin client header required'},403)
            origin = request.headers.get('origin')
            if origin and origin != str(request.base_url).rstrip('/'):
                return JSONResponse({'detail':'Origin rejected'},403)
        response = await call_next(request)
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'"
        return response

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        return JSONResponse({'detail':str(exc)},409)
    @app.exception_handler(KeyError)
    async def missing(request,exc):
        return JSONResponse({'detail':'Task not found'},404)
    @app.get('/api/health')
    def health():
        with store.connect() as c:
            c.execute('SELECT 1')
        return {'status':'ok','inference':type(backend).__name__,'model':getattr(backend,'model','mock'),
                'timezone':os.getenv('BUTLER_TIMEZONE','Europe/Monaco'),'autonomy':'disabled'}
    @app.get('/api/state')
    def state():
        return {t:store.rows(t) for t in ('tasks','calendar','audit')}
    @app.get('/api/integrations')
    def integrations():
        return [{'name':'Calendar','mode':'mock','actions':'approval required'},
                {'name':'Email','mode':'mock','actions':'draft listing only; sending disabled'}]
    @app.post('/api/tasks')
    async def submit(request: Request):
        return await service.submit(request.text,request.key)
    @app.post('/api/tasks/{task_id}/decision')
    def decide(task_id: str,decision: Decision):
        return service.decide(task_id,decision.approve)
    if (ROOT/'frontend/dist').exists():
        app.mount('/assets',StaticFiles(directory=ROOT/'frontend/dist/assets'),name='assets')
        @app.get('/')
        def index():
            return FileResponse(ROOT/'frontend/dist/index.html')
    return app
