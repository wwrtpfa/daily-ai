"""Exercise publication gates using isolated copies; never edit real editions."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

spec=importlib.util.spec_from_file_location('validator',Path(__file__).with_name('validate-content.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
original=v.ROOT

def case(name,mutate,should_fail=True):
    with tempfile.TemporaryDirectory(prefix='signal-validation-') as temp:
        root=Path(temp)
        shutil.copytree(original/'content',root/'content')
        shutil.copytree(original/'config',root/'config')
        path=sorted((root/'content/days').glob('*.json'))[-1]
        d=json.loads(path.read_text());mutate(d,root);path.write_text(json.dumps(d))
        v.ROOT=root
        try:
            v.run()
        except (AssertionError, ValueError):
            assert should_fail, name
        else:
            assert not should_fail, f'{name}: invalid content accepted'
        finally:v.ROOT=original
        print('PASS:',name)

case('valid canonical edition',lambda d,r:None,False)
case('missing facts rejected',lambda d,r:d['items'][0].update(facts=[]))
case('source outside window rejected',lambda d,r:d['items'][2]['sources'][0].update(publishedAt='2025-01-01T00:00:00Z'))
case('brief mismatch rejected',lambda d,r:d['brief'].reverse())
def duplicate(d,r):
    d['items'][1]['sources']=d['items'][0]['sources']
case('duplicate event sources rejected',duplicate)
def metric(d,r):
    p=r/'content/projects'/f'{d["date"]}.json';data=json.loads(p.read_text());data['projects'][0]['day']['delta']=42;p.write_text(json.dumps(data))
case('invented delta without baseline rejected',metric)
