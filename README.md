# destrucTG
Инструмент для автоматического сбора и отправки постов в Telegram.

## Зачем это нужно?
Если интересна идеологическая сторона вопроса – читайте [манифест](/manifesto.md).

Если техническая – это бот, который берёт посты с заданных вами каналов и (с массой условий и настроек) постит их к вам. Подробнее читайте ниже.

## Конфигурация
Откройте файл `config.json` в любом текстовом редакторе и измените соответствующие параметры:

```
{
  "client_session_name": "destrucTG",  // имя сессии для клиента, можно оставить нетронутым
  "bot_session_name": "destrucTG_bot", // имя сессии для бота, можно оставить нетронутым
  "api_id": 12345678,                  // api_id, можно получить на my.telegram.org
  "api_hash": "hash",                  // api_hash, можно получить на my.telegram.org
  "bot_token": "TOKEN",                // токен бота, можно получить у @BotFather в Telegram
  "main_admin": 1234567890,            // User ID главного администратора бота 
  "target_channel": "@target"          // username, ID или ссылка на целевой канал
}
```

### client_session_name и bot_session_name
Можно оставить стандартными, можно поменять, это ни на что не влияет.

### api_id и api_hash
Можно получить на [my.telegram.org](https://my.telegram.org), залогинившись через свой Telegram-аккаунт и создав новый клиент.

### bot_token
Можно получить, создав нового бота через [@BotFather](https://t.me/BotFather). Именно этот бот впоследствии будет использоваться для управления постингом.

### main_admin
User ID основного админа, который можно получить, либо посмотрев в сторонних клиентах (таких как Nekogram), либо в одном из многочисленных ботов для получения своего User ID ([пример](https://t.me/UserInfoToBot)) 

### target_channel
Канал, в который в итоге будет производиться постинг. Может быть как в формате @username, так и ID или ссылки

### Аккаунт-сборщик

Помимо вышеперечисленной конфигурации, вам понадобится специальный пользовательский аккаунт Telegram, который должен быть подписан на интересующие вас источники постов. Это может быть как ваш основной аккаунт, так и второй, созданный специально для этого. В этот аккаунт вам необходимо будет залогиниться на этапе запуска.
## Запуск

Первым делом установите `python` и `git` актуальной версии на ваш компьютер.

Далее введите в терминале следующие команды:

```
git clone https://github.com/desup6/destrucTG.git
cd destructTG
python -m venv .venv
```

Для Windows:

```
.venv\Scripts\activate.bat
.venv\bin\pip install -r requirements.txt
.venv\bin\python main.py
```

Для Linux/MacOS:

```
source .venv/bin/activate
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

Далее будет необходимо войти в аккаунт-сборщик, введя номер привязанный к нему номер телефона и код подтверждения. После этого отправьте созданному вами боту `/start`, и запуск можно считать успешным.

## Использование

После отправки `/start` боту, перед вами появится сообщение-меню, с помощью которого можно управлять настройками бота. Для базового использования достаточно указать интересующие источники с помощью `Manage Sources` -> `Add Source`.

## TODO:

- более развёрнутый гайд по использованию
- поддержка альбомов

## Поддержка

Лучшей поддержкой будет вклад в разработку. Пишите Issues, присылайте Pull Requests, распространяйте destrucTG.