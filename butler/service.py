import json
import logging
from uuid import uuid4
from .models import Schedule
from .connectors import MockCalendar

log = logging.getLogger("butler")

class Conflict(Exception): pass

class Service:
    def __init__(self, store, inference):
        self.store, self.inference, self.calendar = store, inference, MockCalendar()

    def event(self, c, task_id, event):
        c.execute("INSERT INTO audit(task_id,event) VALUES (?,?)", (task_id,event))
        log.info(json.dumps({'event':event,'task_id':task_id}))

    def task(self, task_id):
        with self.store.connect() as c:
            row = c.execute('SELECT * FROM tasks WHERE id=?',(task_id,)).fetchone()
            if not row:
                raise KeyError(task_id)
            return dict(row)

    async def submit(self, text, key):
        task_id = str(uuid4())
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            old = c.execute('SELECT * FROM tasks WHERE request_key=?',(key,)).fetchone()
            if old:
                if old['request'] != text:
                    raise Conflict('Idempotency key already used for another request')
                return dict(old)
            c.execute("INSERT INTO tasks(id,request_key,request,state) VALUES (?,?,?,'extracting')",(task_id,key,text))
            self.event(c,task_id,'extraction_started')
        try:
            proposal = await self.inference.extract(text)
            with self.store.connect() as c:
                state = 'conflict' if self.calendar.conflicts(c,proposal) else 'pending_approval'
                c.execute('UPDATE tasks SET state=?,proposal=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',
                          (state,proposal.model_dump_json(),task_id))
                c.execute("INSERT INTO memory(kind,content,provenance,confidence) VALUES ('episode',?,?,1)",
                          ('Scheduling proposal extracted',task_id))
                self.event(c,task_id,state)
        except Exception as exc:
            # Never persist upstream response bodies or arbitrary exception text.
            message = 'Could not extract a valid schedule. Specify title, date, start, end and timezone; check model availability.'
            with self.store.connect() as c:
                c.execute("UPDATE tasks SET state='failed',error=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(message,task_id))
                self.event(c,task_id,'extraction_failed')
            log.info(json.dumps({'event':'inference_failure','type':type(exc).__name__}))
        return self.task(task_id)

    def decide(self, task_id, approve):
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row = c.execute('SELECT * FROM tasks WHERE id=?',(task_id,)).fetchone()
            if not row:
                raise KeyError(task_id)
            target = 'completed' if approve else 'rejected'
            if row['state'] == target:
                return dict(row)
            if row['state'] not in ('pending_approval','conflict'):
                raise Conflict('Task cannot be changed in its current state')
            if approve:
                proposal = Schedule.model_validate_json(row['proposal'])
                if self.calendar.conflicts(c,proposal):
                    raise Conflict('Calendar conflict: reject and submit a different time')
                self.event(c,task_id,'approved')
                self.calendar.create(c,task_id,proposal)
                c.execute("INSERT INTO memory(kind,content,provenance,confidence) VALUES ('commitment',?,?,1)",
                          (row['proposal'],task_id))
            c.execute('UPDATE tasks SET state=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(target,task_id))
            self.event(c,task_id,target)
        return self.task(task_id)

    def recover(self):
        with self.store.connect() as c:
            for row in c.execute("SELECT id FROM tasks WHERE state='extracting'").fetchall():
                c.execute("UPDATE tasks SET state='interrupted',error='Interrupted during extraction; resubmit with a new key' WHERE id=?",(row['id'],))
                self.event(c,row['id'],'interrupted')
