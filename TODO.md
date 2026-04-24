# TODO

- [x] 1. Создать backend FastAPI для кредитного скоринга
  - [x] 1.1 Добавить `project/backend/main.py` с обучением baseline модели
  - [x] 1.2 Добавить endpoint `POST /predict`
  - [x] 1.3 Добавить endpoint `GET /metrics`
  - [x] 1.4 Добавить `project/backend/requirements.txt`

- [x] 2. Создать Flutter frontend
  - [x] 2.1 Добавить `project/frontend/pubspec.yaml`
  - [x] 2.2 Добавить `project/frontend/lib/main.dart` с формой из 8 полей
  - [x] 2.3 Добавить вызов backend `/predict` и вывод результата

- [x] 3. Добавить документацию запуска
  - [x] 3.1 Добавить `project/README.md` с инструкцией backend/frontend

- [ ] 4. Проверить команды запуска
  - [ ] 4.1 Backend: `uvicorn main:app --reload`
  - [ ] 4.2 Frontend: `flutter pub get` и `flutter run`
