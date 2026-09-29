"""Prepare a LinkedIn draft; does NOT automate LinkedIn or send applications."""
import argparse
from pathlib import Path
from urllib.parse import urlsplit
from agent import make_draft, read_db, save

def main():
    p=argparse.ArgumentParser(description='Только черновик LinkedIn. Отправки нет.')
    p.add_argument('job_id'); p.add_argument('--data-dir',type=Path,default=Path.cwd()/'my-job-agent-data')
    a=p.parse_args()
    try:
        db=read_db(a.data_dir)
        job=next((j for j in db['jobs'] if j['id']==a.job_id),None)
        if not job: raise ValueError('Вакансия не найдена')
        host=urlsplit(job['url']).hostname or ''
        if host!='linkedin.com' and not host.endswith('.linkedin.com'):
            raise ValueError('Это не ссылка LinkedIn')
        path=make_draft(db,a.job_id,a.data_dir)
        save(a.data_dir/'jobs.json',db)
        print('Черновик создан, заявка НЕ отправлена:',path)
    except (ValueError,OSError) as exc: p.exit(1,str(exc)+'\n')

if __name__=='__main__': main()
