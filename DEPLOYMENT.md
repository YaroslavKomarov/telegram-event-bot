# 🚀 Развертывание Telegram бота на Railway

## 📋 Пошаговая инструкция

### Шаг 1: Подготовка GitHub репозитория

1. **Создайте репозиторий на GitHub:**
   - Зайдите на [github.com](https://github.com)
   - Создайте новый репозиторий (например, `telegram-event-bot`)
   - Сделайте его публичным или приватным

2. **Загрузите код:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/ВАШ_USERNAME/telegram-event-bot.git
   git push -u origin main
   ```

### Шаг 2: Регистрация на Railway

1. **Перейдите на [railway.app](https://railway.app)**
2. **Войдите через GitHub** (рекомендуется)
3. **Подтвердите email** если потребуется

### Шаг 3: Создание проекта

1. **Нажмите "New Project"**
2. **Выберите "Deploy from GitHub repo"**
3. **Выберите ваш репозиторий** `telegram-event-bot`
4. **Railway автоматически определит Python проект**

### Шаг 4: Добавление PostgreSQL базы данных

1. **В проекте нажмите "Add Service"**
2. **Выберите "Database" → "PostgreSQL"**
3. **Railway автоматически создаст базу данных**
4. **Скопируйте переменные подключения** (появятся автоматически)

### Шаг 5: Настройка переменных окружения

В разделе **Variables** добавьте:

```env
# Telegram бот
BOT_TOKEN=8087345371:AAHUr4ZS1qSJ7BiHaHFA9NglilEAiT5GiNs
ADMIN_CHAT_ID=-1002726221776
CHANNEL_ID=-1002711080390

# База данных (автоматически создается Railway)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Для локальной разработки (опционально)
PGHOST=${{Postgres.PGHOST}}
PGDATABASE=${{Postgres.PGDATABASE}}
PGUSER=${{Postgres.PGUSER}}
PGPASSWORD=${{Postgres.PGPASSWORD}}
PGPORT=${{Postgres.PGPORT}}
```

### Шаг 6: Изменение основного файла бота

**Измените импорт базы данных** в `bot.py`:

```python
# Заменить эту строку:
# from database import db

# На эту:
from database_railway import db
```

**Аналогично в других файлах** (`handlers.py`, `callbacks.py`):
```python
from database_railway import db
```

### Шаг 7: Деплой

1. **Сохраните изменения в Git:**
   ```bash
   git add .
   git commit -m "Add Railway deployment config"
   git push
   ```

2. **Railway автоматически запустит деплой**
3. **Следите за логами** в интерфейсе Railway
4. **Дождитесь статуса "Success"**

### Шаг 8: Проверка работы

1. **Проверьте логи** в Railway Dashboard
2. **Протестируйте бота** в Telegram
3. **Убедитесь что база данных работает**

---

## 🔧 Альтернативные платформы

### Option 2: Render.com (Бесплатно)

**Плюсы:**
- Полностью бесплатный tier
- PostgreSQL включена
- Простой деплой

**Минусы:**
- Засыпает после 15 минут неактивности
- Медленный "холодный" старт

**Инструкции:**
1. Зарегистрируйтесь на [render.com](https://render.com)
2. Создайте Web Service из GitHub репозитория
3. Добавьте PostgreSQL в Services
4. Настройте переменные окружения

### Option 3: Fly.io (Почти бесплатно)

**Плюсы:**
- Очень быстрый
- Не засыпает
- Отличная производительность

**Минусы:**
- Требует кредитную карту
- Чуть сложнее настройка

**Инструкции:**
1. Установите `flyctl`
2. Запустите `fly launch`
3. Добавьте PostgreSQL через `fly postgres create`

---

## 💰 Стоимость Railway

- **Бесплатный пробный период:** $5 кредитов
- **Hobby Plan:** $5/месяц
- **PostgreSQL:** Включена в план
- **Хватит на:** 720 часов работы бота

## 🔍 Мониторинг

### Логи Railway
```bash
# Локально через CLI
railway logs

# Или в веб-интерфейсе
railway.app → ваш проект → Logs
```

### Проверка состояния
- **Metrics** - использование ресурсов
- **Deployments** - история деплоев
- **Settings** - настройки проекта

---

## 🚨 Устранение проблем

### Бот не отвечает
1. Проверьте переменные окружения
2. Посмотрите логи Railway
3. Убедитесь что BOT_TOKEN правильный

### Ошибки базы данных
1. Проверьте DATABASE_URL
2. Убедитесь что PostgreSQL сервис запущен
3. Проверьте подключение в логах

### Деплой не работает
1. Проверьте requirements.txt
2. Убедитесь что все файлы загружены
3. Проверьте runtime.txt (Python версия)

---

## ✅ Финальный чеклист

- [ ] Репозиторий создан на GitHub
- [ ] Код загружен в репозиторий  
- [ ] Railway проект создан
- [ ] PostgreSQL добавлена
- [ ] Переменные окружения настроены
- [ ] Импорты изменены на database_railway
- [ ] Деплой успешно завершен
- [ ] Бот отвечает в Telegram
- [ ] База данных работает

**🎉 Поздравляем! Ваш бот успешно развернут!** 