# Credit Scoring Solution (Flutter + FastAPI)

Решение хакатон-задачи на основе baseline из `Hackaton/baseline.ipynb`.

## Что реализовано

- **Backend:** `project/backend/main.py` (FastAPI)
  - Обучение baseline логистической регрессии на старте (numpy/pandas)
  - `POST /predict` — скоринг новой заявки
  - `GET /metrics` — ROC-AUC, PR-AUC, Accuracy@0.5
  - `GET /health` — проверка сервиса

- **Frontend:** `project/frontend/lib/main.dart` (Flutter)
  - Форма ввода всех 8 признаков
  - Вызов backend `/predict`
  - Отображение результата:
    - `default / non-default`
    - `P(default)` и `P(non-default)`
    - метрики модели

## Признаки (должны передаваться все)

1. `age`
2. `monthly_income`
3. `employment_years`
4. `loan_amount`
5. `loan_term_months`
6. `interest_rate`
7. `past_due_30d`
8. `inquiries_6m`

## Запуск backend (FastAPI)

Из корня репозитория:

```bash
cd project/backend
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Backend по умолчанию: `http://127.0.0.1:8000`

Проверка:
- `GET http://127.0.0.1:8000/health`
- `GET http://127.0.0.1:8000/metrics`

Пример запроса на скоринг:

```bash
curl -X POST "http://127.0.0.1:8000/predict" ^
  -H "Content-Type: application/json" ^
  -d "{\"age\":29,\"monthly_income\":32000,\"employment_years\":3.5,\"loan_amount\":650000,\"loan_term_months\":48,\"interest_rate\":33,\"past_due_30d\":2,\"inquiries_6m\":4}"
```

## Запуск frontend (Flutter)

```bash
cd project/frontend
flutter pub get
flutter run
```

### Важно про адрес backend
В `lib/main.dart` установлен:
- `http://10.0.2.2:8000` — для Android эмулятора.

Если запускаете Flutter Web/Desktop или iOS simulator, замените `_apiBaseUrl` на:
- `http://127.0.0.1:8000` или
- IP вашего ПК в локальной сети.

## Архитектура модели

Ровно как в baseline:
- train/test split 80/20 (`seed=42`)
- стандартизация по train (`mu`, `sd`)
- логистическая регрессия (градиентный спуск)
- порог `0.5`

Возвращаем:
- `label`: `default` или `non-default`
- `p_default`, `p_non_default`
- `metrics`
