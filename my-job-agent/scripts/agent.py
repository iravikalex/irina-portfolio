"""Local job journal and draft assistant. Python 3.10+, standard library only."""
import argparse
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]

def now():
    return datetime.now(timezone.utc).isoformat()

def config(name):
    path = ROOT / 'config' / (name + '.yaml')
    if name == 'profile' and not path.exists():
        path = ROOT / 'config' / 'profile.example.yaml'
    return json.loads(path.read_text(encoding='utf-8'))

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)

def read_db(directory):
    path = directory / 'jobs.json'
    if not path.exists():
        return {'schema_version': 1, 'jobs': [], 'runs': []}
    value = json.loads(path.read_text(encoding='utf-8'))
    if value.get('schema_version') != 1 or not isinstance(value.get('jobs'), list) or not isinstance(value.get('runs'), list):
        raise ValueError('Неверная схема журнала. Исходный файл сохранён.')
    return value

def clean(value):
    return html.unescape(re.sub('<[^>]+>', ' ', str(value or ''))).strip()

def normalize(row):
    if not isinstance(row, dict):
        raise ValueError('Вакансия должна быть объектом')
    for key in ('source', 'title', 'url'):
        if not isinstance(row.get(key), str) or not row[key].strip():
            raise ValueError('Отсутствует поле ' + key)
    u = urlsplit(row['url'].strip())
    if u.scheme != 'https' or not u.hostname or u.username or u.password:
        raise ValueError('Нужна публичная HTTPS-ссылка вакансии')
    url = urlunsplit((u.scheme, u.netloc.lower(), u.path, u.query, ''))
    source = row['source'].strip().lower()
    identity = hashlib.sha256((source + '\n' + url).encode()).hexdigest()[:16]
    out = {k: row.get(k) for k in ('company', 'published_at', 'salary', 'location')}
    out.update(id=identity, source=source, url=url, title=clean(row['title']), description=clean(row.get('description')), checked_at=now(), status='new')
    return out

def merge(db, rows):
    # Validate entire batch before modifying anything.
    items = [normalize(row) for row in rows]
    indexed = {j['id']: j for j in db['jobs']}
    added = 0
    for item in items:
        old = indexed.get(item['id'])
        if old:
            item['status'] = old['status']
            for field in ('draft_path', 'first_seen', 'sent_at', 'confirmation', 'score', 'reasoning', 'reviewed_at'):
                if field in old:
                    item[field] = old[field]
            old.update(item)
        else:
            item['first_seen'] = now()
            db['jobs'].append(item)
            indexed[item['id']] = item
            added += 1
    return added

def fetch(url):
    request = Request(url, headers={'User-Agent': 'MyJobAgent/1.0', 'Accept': 'application/json'})
    with urlopen(request, timeout=25) as response:
        raw = response.read(12_000_001)
    if len(raw) > 12_000_000:
        raise ValueError('Ответ слишком большой')
    return json.loads(raw)

def assess(job):
    t = (job['title'] + ' ' + job['description']).lower()
    score = 0
    reasons = []
    for group in [('контент','content'), ('карточ','маркетплейс','marketplace'), ('дизайн','design','canva','figma'), ('чат','chat','копирайт')]:
        if any(x in t for x in group):
            score += 20
    if any(x in t for x in ('без опыта','junior','помощник')):
        score += 10
    for phrase in ('выкуп за свой счёт','оплатить доступ','оформить займ','вымышленный отзыв'):
        if phrase in t:
            reasons.append('Проверить риск: ' + phrase)
    if any(x in t for x in ('english','английск')):
        reasons.append('Проверить требование английского')
    if any(x in t for x in ('одежд','обув')):
        reasons.append('Проверить категорию товара')
    if not job.get('salary'):
        reasons.append('Оплата не указана')
    reasons.append('Проверить полный текст, график и допустимую страну')
    return min(score, 100), reasons

def make_draft(db, job_id, directory):
    job = next((j for j in db['jobs'] if j['id'] == job_id), None)
    if not job:
        raise ValueError('Вакансия не найдена')
    if job['status'] in ('sent', 'replied', 'closed', 'rejected', 'unknown'):
        raise ValueError('Проверь историю: статус ' + job['status'])
    profile = config('profile')
    text = ('Здравствуйте! Меня зовут Ирина. Меня заинтересовало ваше предложение «' + job['title'] + '». '
            'Хотела бы обсудить задачу и требования к результату.\n\n'
            'Моё портфолио: ' + profile['portfolio'] + '\n\n'
            'Подскажите, пожалуйста, какой объём работы и срок выполнения вы планируете?\n')
    path = directory / 'drafts' / (job_id + '.txt')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError('Черновик уже существует; отредактируй его без перезаписи')
    path.write_text(text, encoding='utf-8')
    job['status'] = 'draft'
    job['draft_path'] = str(path.resolve())
    return path

def main():
    p = argparse.ArgumentParser(description='Импорт, оценка и черновики. Ничего не отправляет.')
    p.add_argument('command', choices=['import','report','draft'])
    p.add_argument('value', nargs='?')
    p.add_argument('--data-dir', type=Path, default=Path.cwd() / 'my-job-agent-data')
    a = p.parse_args()
    try:
        db = read_db(a.data_dir)
        if a.command == 'import':
            if not a.value:
                p.error('Укажи JSON-файл')
            rows = json.loads(Path(a.value).read_text(encoding='utf-8'))
            if not isinstance(rows, list):
                raise ValueError('Нужен JSON-массив вакансий')
            count = merge(db, rows)
            db['runs'].append({'at': now(), 'source': 'import', 'added': count})
            save(a.data_dir / 'jobs.json', db)
            print('Добавлено:', count)
        elif a.command == 'draft':
            path = make_draft(db, a.value, a.data_dir)
            save(a.data_dir / 'jobs.json', db)
            print('Базовый черновик (адаптировать перед отправкой):', path)
        else:
            result = []
            for j in db['jobs']:
                if j['status'] in ('closed', 'rejected', 'sent', 'replied'):
                    continue
                score, checks = assess(j)
                result.append({'id':j['id'],'title':j['title'],'score_hint':score,'checks':checks,'url':j['url'],'status':j['status']})
            print(json.dumps(sorted(result,key=lambda x:x['score_hint'],reverse=True),ensure_ascii=False,indent=2))
    except (ValueError, OSError) as exc:
        p.exit(1, 'Ошибка: ' + str(exc) + '\n')

if __name__ == '__main__':
    main()
