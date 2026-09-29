"""Apply explicit agent reviews, saving high-scoring letters as drafts only."""
import argparse
import json
from pathlib import Path
from agent import ROOT, now, read_db, save
from run import report

def apply_reviews(directory, reviews):
    db=read_db(directory)
    jobs={j['id']:j for j in db['jobs']}
    if not isinstance(reviews,list): raise ValueError('Нужен список оценок')
    seen=set(); plans=[]
    for review in reviews:
        if not isinstance(review,dict): raise ValueError('Оценка должна быть объектом')
        jid=review.get('job_id'); score=review.get('score')
        if jid not in jobs or jid in seen: raise ValueError('Неизвестный или повторный job_id')
        seen.add(jid)
        if type(score) is not int or not 1<=score<=10: raise ValueError('Оценка — целое число 1–10')
        reason=review.get('reasoning')
        if not isinstance(reason,str) or not reason.strip(): raise ValueError('Нужно обоснование')
        job=jobs[jid]
        if job['status'] not in ('new','draft'): raise ValueError('Сначала проверь историю заявки: '+job['status'])
        path=directory/'drafts'/('cover_letter_'+jid+'.md')
        letter=review.get('letter')
        if score>=8:
            if not isinstance(letter,str) or not letter.strip(): raise ValueError('Для 8+ нужен текст отклика')
            if path.exists() or job.get('draft_path'): raise ValueError('Черновик уже существует; редактируй отдельно')
        plans.append((job,score,reason,letter,path))
    # Whole batch validated before mutation.
    for job,score,reason,letter,path in plans:
        job.update(score=score,reasoning=reason,reviewed_at=now())
        if score>=8:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(letter.strip()+'\n',encoding='utf-8')
            job.update(status='draft',draft_path=str(path.resolve()))
    save(directory/'jobs.json',db)
    report(directory)
    return len(plans)

def main():
    p=argparse.ArgumentParser(description='Применить оценки GPT и сохранить черновики. Ничего не отправляет.')
    p.add_argument('reviews',type=Path)
    p.add_argument('--data-dir',type=Path,default=ROOT/'my-job-agent-data')
    a=p.parse_args()
    try: print('Обработано:',apply_reviews(a.data_dir,json.loads(a.reviews.read_text(encoding='utf-8'))))
    except (OSError,ValueError) as exc: p.exit(1,str(exc)+'\n')

if __name__=='__main__': main()
