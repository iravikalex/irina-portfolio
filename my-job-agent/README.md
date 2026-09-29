# Партизан-метод v0.1

Помощник собирает вакансии, ведёт журнал и формирует отчёт. GPT в чате или другом агентном окружении читает полный текст, оценивает соответствие профилю и пишет отклики. При оценке 8–10 отклик сохраняется в черновиках. Отправка не реализована: решение остаётся за пользователем.

## Что работает

- Публичные API HH и Remote OK (при доступности сети).
- Импорт вакансий с любых площадок из JSON.
- Удаление дублей, сохранение статуса заявки и защита черновика от перезаписи.
- Отчёт `my-job-agent-data/daily_report.md`.
- Применение оценки GPT 1–10 и сохранение персонализированного текста при 8+.
- GitHub Actions: тесты и ручной запуск чтения публичных вакансий. Расписание не включено.

Kwork, Workzilla, Freelance.ru, FL.ru, Indeed, LinkedIn и Glassdoor не имеют здесь автоматических коннекторов. Их вакансии поступают через доступный агенту поиск или импорт. Вход в аккаунты и браузерная отправка не настроены. `apply_linkedin.py` готовит только базовый черновик.

## Первый запуск на Windows

Нужен Python 3.10 или новее. В папке `my-job-agent`:

```powershell
Copy-Item config/profile.example.yaml config/profile.yaml
python scripts/run.py --source hh
```

Заполни `config/profile.yaml` своими подтверждёнными данными; файл игнорируется Git. `.yaml` здесь использует JSON-синтаксис, совместимый с YAML 1.2. Местонахождение, минимальная оплата и навыки не угадываются.

Для дополнительного англоязычного источника:

```powershell
python scripts/run.py --source remoteok
```

Remote OK часто содержит требования к английскому и стране. Агент обязан их проверить. Источник: [Remote OK](https://remoteok.com), оригинальные ссылки сохраняются. Ошибка API не равна отсутствию вакансий.

## Цикл с GPT

1. Собрать вакансии скриптом либо импортировать JSON.
2. Передать агенту `AGENTS.md`, локальный профиль и `my-job-agent-data/jobs.json`. Агент открывает полные тексты и выполняет четыре skills.
3. Агент создаёт `my-job-agent-data/reviews.json`:

```json
[
  {
    "job_id": "точный id из jobs.json",
    "score": 8,
    "reasoning": "Обоснование по проверенному тексту вакансии и профилю",
    "letter": "Персонализированный честный отклик"
  }
]
```

4. Применить оценки:

```powershell
python scripts/review.py my-job-agent-data/reviews.json
```

5. Прочитать отчёт и черновики. Отправить выбранное вручную либо отдельно поручить отправку агенту с разрешённым доступом к площадке. Этот код ничего не отправляет.

## Импорт

JSON-массив: обязательны `source`, `title`, `url` (HTTPS); необязательны `description`, `company`, `published_at`, `salary`, `location`. Для анализа нужен полный текст в description или доступная ссылка.

```powershell
python scripts/run.py --source import --input vacancies.json
python scripts/run.py --source existing
python -m unittest discover -s tests -v
```

## GitHub Actions

После принятия изменений в main: Actions → Partizan public search → Run workflow. Можно выбрать HH или Remote OK. Скачиваемый результат содержит только публичные вакансии и отчёт без личного профиля. Каждое облачное выполнение начинается с пустого журнала. Постоянный журнал и черновики ведутся локально; для их облачного хранения нужен отдельный приватный проект.

В публичный репозиторий не загружать личный профиль, черновики, контакты работодателей, пароли или cookies. Автоматизация не обходит ограничения сайтов. CAPTCHA и вход выполняет пользователь. Для v0.1 LangChain/CrewAI/AutoGen, Playwright и Selenium не нужны: они не дают разрешения на доступ к закрытым площадкам.

Документация: [HH API](https://api.hh.ru/openapi/redoc), [Remote OK API](https://remoteok.com/faq), [GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).
