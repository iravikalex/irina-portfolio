"""Collect vacancies and write a report. No sending, no LLM API required."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from agent import ROOT, assess, merge, now, read_db, save

def report(directory):
    db = read_db(directory)
    lines = ['# Партизан — отчёт', '', 'Проверено: ' + now(), '',
             'Автоматический приоритет по словам не заменяет оценку полного текста агентом.', '']
    for job in sorted(db['jobs'], key=lambda j: assess(j)[0], reverse=True):
        if job['status'] in ('closed', 'rejected'):
            continue
        hint, checks = assess(job)
        # Escape Markdown metacharacters in untrusted titles.
        title = job['title'].replace('\n',' ').replace('#','').replace('[','(').replace(']',')')
        lines += ['## ' + title, '', 'ID: ' + job['id'], '',
                  'Источник: ' + job['source'] + ' — ' + job['url'], '',
                  'Статус: ' + job['status'], '',
                  'Оценка агента: ' + str(job.get('score', 'ещё не выполнена')), '',
                  'Приоритет по ключевым словам: ' + str(hint) + '/100', '',
                  'Оплата: ' + json.dumps(job.get('salary'), ensure_ascii=False), '',
                  'Проверить: ' + '; '.join(checks), '']
        if job.get('reasoning'):
            lines += ['Обоснование: ' + job['reasoning'], '']
        if job.get('draft_path'):
            lines += ['Черновик: ' + job['draft_path'], '']
    if not db['jobs']:
        lines += ['Вакансии пока не собраны. При ошибке источника это не означает отсутствие вакансий.', '']
    for run in db['runs'][-10:]:
        if run.get('errors') or run.get('error'):
            lines += ['Ошибка источника: ' + json.dumps(run,ensure_ascii=False), '']
    directory.mkdir(parents=True,exist_ok=True)
    path=directory/'daily_report.md'
    path.write_text('\n'.join(lines),encoding='utf-8')
    return path

def main():
    p=argparse.ArgumentParser(description='Партизан: сбор → отчёт → оценка GPT → черновики → решение пользователя')
    p.add_argument('--source',choices=['hh','remoteok','import','existing'],default='existing')
    p.add_argument('--input',type=Path)
    p.add_argument('--data-dir',type=Path,default=ROOT/'my-job-agent-data')
    a=p.parse_args(); code=0
    if a.source in ('hh','remoteok'):
        code=subprocess.run([sys.executable,str(ROOT/'scripts'/('search_'+a.source+'.py')),'--data-dir',str(a.data_dir)]).returncode
    elif a.source=='import':
        if not a.input: p.error('--input обязателен для импорта')
        rows=json.loads(a.input.read_text(encoding='utf-8'))
        if not isinstance(rows,list): p.error('Нужен JSON-массив')
        db=read_db(a.data_dir); added=merge(db,rows)
        db['runs'].append({'at':now(),'source':'import','added':added})
        save(a.data_dir/'jobs.json',db)
    print(report(a.data_dir))
    if code: p.exit(code,'Источник вернул ошибку; смотри отчёт.\n')

if __name__=='__main__': main()
