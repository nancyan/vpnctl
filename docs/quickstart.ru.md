# vpnctl: быстрый старт на русском

## Назначение

`vpnctl` — двуязычная консоль управления инфраструктурой на базе Ansible. Процедуры намеренно разделены:

1. `doctor` — проверяет локальный компьютер, не подключаясь к серверам.
2. `keys` — создаёт UUID и short ID; ключи REALITY генерируются только через установленный Xray (`keys --xray-binary xray`).
3. `validate` — проверяет связи и обязательные поля приватной топологии.
4. `plan` — выводит список предварительных требований без подключения к VPS.
5. `render` — формирует отдельные конфигурации Xray и фрагменты NGINX Stream для каждого узла.
6. `bootstrap` — подготавливает **только новый тестовый VPS** с ручным маркером допуска и обязательным подтверждением.
7. `stage` — передаёт конфигурацию Xray на **тестовый VPS** без запуска и перезапуска служб.

## Подготовка

На Windows используйте WSL. Требуются Python 3.10+, SSH, Ansible и rsync.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yml
python3 vpnctl.py --lang ru doctor
```

## Генерация топологии локально

```bash
python3 vpnctl.py --lang ru keys
python3 vpnctl.py --lang ru keys --xray-binary xray
cp examples/topology.example.json topology.local.json
# Заменить все демонстрационные значения собственными сгенерированными ключами.
python3 vpnctl.py --lang ru validate --topology topology.local.json
python3 vpnctl.py --lang ru plan --topology topology.local.json
python3 vpnctl.py --lang ru render --topology topology.local.json --output rendered
```

**Пример topology.example.json заведомо не запускается**: поля ключей REALITY — заглушки. `rendered/**/xray.json` содержит секреты и не должен попадать в GitHub. Фрагмент NGINX Stream — только пример включения во внутренний `stream {}`, а не полный конфиг. Учтите конфликты порта 443, сертификаты и SNI.

## Тестовый VPS

В приватном `inventory/local.yml` укажите имя тестового узла, совпадающее с названием папки в `rendered`, и `vpnctl_fresh_host: true`. На **тестовом** сервере вручную создайте `/etc/vpnctl-allow-bootstrap`; на рабочих VPS не создавайте.

```bash
python3 vpnctl.py --inventory inventory/local.yml bootstrap --host eu_exit --confirm-fresh-vps --apply
python3 vpnctl.py --inventory inventory/local.yml stage --host eu_exit --confirm-fresh-vps --bundle rendered --apply
```

Подтверждение `APPLY` обязательно. `bootstrap` отклоняет серверы с существующим `x-ui.service` или `xray.service`. `stage` отклоняет 3x-ui, копирует конфигурацию в `/etc/vpnctl/staged/xray.json` и при наличии Xray выполняет проверку синтаксиса. **VPN автоматически не активируется**. Playbook пока экспериментальные, на реальном тестовом VPS не апробированы.

## Ограничения

Пока нет автоматической выдачи сертификатов, настройки существующего 3x-ui, запуска Stream на 443, активации сгенерированной конфигурации Xray, настройки пользовательских профилей и рабочего переключения между выходными узлами. Успешный `stage` не означает, что VPN подключается.

## Экспериментальная активация (только одноразовый тестовый VPS)

После `bootstrap` и `stage` разрешается **отдельно** активировать уже проверенную Xray-конфигурацию. До этого должны быть вручную подготовлены DNS, HTTPS-сертификат, локальная HTTPS-страница на `127.0.0.1:9443`, NGINX Stream на `443`, firewall и проверены зависимости. Генерируемый `nginx-stream.conf.example` **не устанавливается автоматически**.

```bash
python3 vpnctl.py --lang ru --inventory inventory/local.yml activate --host eu_exit --confirm-fresh-vps --apply
```

Команда требует интерактивный ввод `APPLY`, защищённый маркер `/etc/vpnctl-allow-bootstrap`, отсутствие 3x-ui и наличие отдельного сервиса `/etc/systemd/system/xray.service`. Предыдущий `/etc/xray/config.json` сохраняется в `/etc/vpnctl/backups/`, кандидат проверяется командой `xray run -test`, затем перезапускается только `xray` и проверяется локальный TCP-порт (по умолчанию 3030). При обнаруженной ошибке Playbook пытается вернуть прежний конфиг и перезапустить Xray. **Откат best-effort, не атомарный и не гарантия восстановления.** Внешнюю доступность VPN, выдачу сертификатов, TLS/SNI и безопасность firewall команда не проверяет. Запуск на производственных серверах запрещён.
