# Антиплагиатная система

## Архитектура

Система состоит из трех микросервисов:
- **API Gateway** (порт 8000): Принимает запросы от клиентов, маршрутизирует к другим сервисам.
- **File Storing Service** (порт 8001): Хранит файлы и метаданные работ в PostgreSQL и файловой системе.
- **File Analysis Service** (порт 8002): Анализирует на плагиат путем сравнения SHA256-хэшей, хранит отчеты в PostgreSQL.

Базы данных:
- PostgreSQL для storing (порт 5433)
- PostgreSQL для analysis (порт 5434)

Общение: HTTP между сервисами.

Контейнеризация: Docker Compose.

## Алгоритм определения плагиата

Плагиат определяется, если SHA256-хэш загруженного файла совпадает с хэшем любой предыдущей работы (побайтовое совпадение).

## User Flow

1. Студент загружает работу: POST /upload (gateway) с student_id (ID студента, строка), assignment_id (ID задания, строка), file (файл работы, любой тип, но сохраняется как octet-stream).
   - Gateway отправляет файл в File Storing.
   - Storing сохраняет файл, вычисляет хэш, сохраняет метаданные (включая student_id и assignment_id).
   - Gateway отправляет хэш и время в File Analysis.
   - Analysis запрашивает предыдущие работы из Storing, проверяет совпадение хэша.
   - Возвращает work_id и report_id.

2. Преподаватель запрашивает отчет: GET /works/{work_id}/reports (gateway).
   - Gateway перенаправляет в Analysis, возвращает JSON с флагом плагиата.

## Как запустить и использовать систему

### Запуск

1. Убедитесь, что Docker и Docker Compose установлены.
2. В корневой директории проекта выполните:
   ```
   docker compose up --build
   ```
   Это соберет и запустит все сервисы: базы данных, микросервисы и gateway.

3. Сервисы будут доступны:
   - Gateway: http://localhost:8000
   - File Storing: http://localhost:8001
   - File Analysis: http://localhost:8002
   - PostgreSQL Storing: localhost:5433 (user: user, pass: pass, db: storing_db)
   - PostgreSQL Analysis: localhost:5434 (user: user, pass: pass, db: analysis_db)

4. Для остановки: `docker compose down`

### Тестирование API

FastAPI предоставляет автоматическую Swagger-документацию:
- Gateway: http://localhost:8000/docs
- Storing: http://localhost:8001/docs
- Analysis: http://localhost:8002/docs

Используйте Swagger UI для интерактивного тестирования эндпоинтов.

#### Примеры с curl

1. **Загрузка работы** (через Gateway, используя файл text1.txt из проекта):
   ```
   curl -X 'POST' \
      'http://localhost:8000/upload' \
      -F 'student_id=dsds' \
      -F 'assignment_id=1' \
      -F 'file=@text1.txt'
   ```
   - student_id: уникальный идентификатор студента (строка, например, "student1").
   - assignment_id: идентификатор задания (строка, например, "math_homework_1").
   - file: файл контрольной работы (например, text1.txt).
   Ответ: JSON с work_id, report_id, plagiarism (для первого файла будет false).

2. **Загрузка второго файла для теста плагиата** (тот же text1.txt, но другой студент):
   ```
   curl -X POST "http://localhost:8000/upload" \
     -F "student_id=student2" \
     -F "assignment_id=math_homework_1" \
     -F "file=@text1.txt"
   ```
   Ответ: JSON с plagiarism=true и matched_work_id (ID первой работы).

3. **Получение отчета по работе** (замените 1 на work_id из ответа):
   ```
   curl -X GET "http://localhost:8000/works/1/reports"
   ```
   Ответ: JSON с деталями отчета (plagiarism, timestamp, matched_work_id).

#### Тестирование плагиата

- Загрузите text1.txt дважды с разными student_id.
- Первый: plagiarism=false
- Второй: plagiarism=true, matched_work_id=первый_id
- Для разных файлов (text1.txt и text2.txt): plagiarism=false.

### Структура проекта

- `docker-compose.yml`: Оркестрация сервисов.
- `gateway/`: API Gateway.
- `file_storing/`: Сервис хранения.
- `file_analysis/`: Сервис анализа.

### Обработка ошибок

Сервисы возвращают HTTP ошибки (4xx/5xx). Если сервис падает, gateway вернет 500. Логи Docker покажут детали: `docker compose logs <service>`.

## API

### Gateway
- POST /upload (multipart: student_id, assignment_id, file) → {work_id, report_id, plagiarism}
- GET /works/{work_id}/reports → {report_id, work_id, plagiarism, timestamp, matched_work_id}

### File Storing
- POST /works (multipart: student_id, assignment_id, file) → {work_id, hash, timestamp}
- GET /previous_works?before={iso_timestamp} → {previous_works: [{id, hash}, ...]}
- GET /works/{work_id}/file → файл

### File Analysis
- POST /analyze/{work_id} (json: {file_hash, upload_time}) → {report_id, plagiarism, matched_work_id}
- GET /reports/{work_id} → {report_id, work_id, plagiarism, timestamp, matched_work_id}

## Дополнительно

- Файлы хранятся в volume `file_storing_files`.
- Для разработки: монтируйте volumes для hot-reload.
- Clean Architecture: Каждый сервис имеет models.py (entities), app.py (use cases + adapters).
