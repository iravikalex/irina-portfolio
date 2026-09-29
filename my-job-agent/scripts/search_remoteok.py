"""Optional Remote OK public feed. Preserve attribution and job links."""
import argparse
from pathlib import Path
from agent import config, fetch, merge, now, read_db, save

def main():
    p=argparse.ArgumentParser(description='Дополнительный поиск Remote OK, обычно на английском.')
    p.add_argument('--data-dir',type=Path,default=Path.cwd()/'my-job-agent-data')
    a=p.parse_args(); cfg=config('platforms')['remoteok']; db=read_db(a.data_dir)
    try:
        data=fetch(cfg['url'])
        if not isinstance(data,list): raise ValueError('Неверный формат API')
        rows=[]
        for j in data:
            if not isinstance(j,dict) or not j.get('position') or not j.get('url'): continue
            text=(j['position']+' '+' '.join(j.get('tags') or [])).lower()
            if not any(k in text for k in cfg['keywords']): continue
            rows.append({'source':'remoteok','title':j['position'],'url':j['url'],'company':j.get('company'),'description':j.get('description'),'published_at':j.get('date'),'location':j.get('location'),'salary':{'from':j.get('salary_min'),'to':j.get('salary_max'),'currency':j.get('salary_currency')} if j.get('salary_min') or j.get('salary_max') else None})
        count=merge(db,rows)
        db['runs'].append({'at':now(),'source':'remoteok','added':count})
        save(a.data_dir/'jobs.json',db)
        print('Источник: Remote OK — https://remoteok.com. Добавлено:',count)
        print('Проверить язык, свежесть и допустимую страну каждой вакансии.')
    except Exception as exc:
        db['runs'].append({'at':now(),'source':'remoteok','error':str(exc)})
        save(a.data_dir/'jobs.json',db)
        p.exit(1,'Ошибка источника (не отсутствие вакансий): '+str(exc)+'\n')

if __name__=='__main__': main()
