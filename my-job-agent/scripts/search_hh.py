"""Read public HH search results; keep original snippets and URLs."""
import argparse
from pathlib import Path
from urllib.parse import urlencode
from agent import config, fetch, merge, now, read_db, save

def main():
    p=argparse.ArgumentParser(description='Поиск HH. Не отправляет отклики.')
    p.add_argument('--data-dir',type=Path,default=Path.cwd()/'my-job-agent-data')
    a=p.parse_args()
    cfg=config('platforms')['hh']
    db=read_db(a.data_dir)
    rows=[]; errors=[]
    for query in cfg['queries']:
        for page in range(cfg['max_pages']):
            try:
                data=fetch(cfg['url']+'?'+urlencode({'text':query,'work_format':'REMOTE','period':cfg['days'],'per_page':50,'page':page,'order_by':'publication_time'}))
                if not isinstance(data,dict) or not isinstance(data.get('items'),list):
                    raise ValueError('Неверный ответ API')
                for j in data['items']:
                    snippet=j.get('snippet') or {}
                    rows.append({'source':'hh','title':j['name'],'url':j['alternate_url'],'company':(j.get('employer') or {}).get('name'),'description':(snippet.get('requirement') or '')+' '+(snippet.get('responsibility') or ''),'salary':j.get('salary'),'location':(j.get('area') or {}).get('name'),'published_at':j.get('published_at')})
                if page+1>=data.get('pages',0): break
            except Exception as exc:
                errors.append({'query':query,'page':page,'error':str(exc)})
                break
    count=merge(db,rows)
    db['runs'].append({'at':now(),'source':'hh','added':count,'errors':errors})
    save(a.data_dir/'jobs.json',db)
    print('Добавлено:',count,'. Полный текст вакансий требует проверки.')
    for error in errors: print('Источник недоступен или ответ неполный:',error)
    if errors: raise SystemExit(1)

if __name__=='__main__': main()
