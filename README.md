# vpnctl — bilingual Ansible infrastructure console / двуязычная Ansible-консоль

[English](#english) | [Русский](#русский)

> **Experimental v0.3** — safe starting point, **not** a complete one-command VPN installer. There is no automatic Xray/3x-ui installation or failover configuration in this release.

## English

`vpnctl` provides a small RU/EN command-line wrapper around Ansible to inspect SSH servers, collect backups, and deploy a static website. It is intended as the **first stage** of managing infrastructure as code, rather than replacing live 3x-ui SQLite-managed configuration.

### Requirements

- Linux/macOS or Windows with WSL; Python 3.10+, SSH, rsync, Ansible; tested locally with Python stdlib. Controller with Ansible required for live use.
- SSH connectivity to your own hosts, with verified host keys and sudo permissions as required.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yml
cp inventory/hosts.yml inventory/local.yml
# edit inventory/local.yml with YOUR addresses and credentials
python3 vpnctl.py --lang en --inventory inventory/local.yml hosts
python3 vpnctl.py --lang en --inventory inventory/local.yml ping --host fi_in_2
python3 vpnctl.py --lang en --inventory inventory/local.yml status --host fi_in_2
python3 vpnctl.py --lang en --inventory inventory/local.yml discover --host fi_in_2
python3 vpnctl.py --lang en --inventory inventory/local.yml backup --host fi_in_2 --apply
python3 vpnctl.py --lang en --inventory inventory/local.yml clock --host fi_in_2 --check
python3 vpnctl.py --lang en --inventory inventory/local.yml clock --host fi_in_2 --apply
```

- `ping`, `status`, and `discover` are read-only; `discover` reports service activity and listening ports, not whether a VPN route is functioning.
- `backup` requires `--apply` and stores sensitive data in `backups/`, which is ignored by Git. Protect/encrypt off-machine backups. The backup playbook needs `rsync` and potentially privileged remote rsync access; validate on a test VPS first.
- `clock --apply` copies static files to `/var/www/adelaide-clock` **only**. It does not change NGINX `root`, TLS, Stream, Xray, 3x-ui or server routing. This is intentional to protect running VPN installations.
- `--check` is best-effort Ansible check mode; not all third-party modules guarantee perfect no-change simulation.
- The example inventory uses documentation-only IPs. **Never commit real panel URLs, UUIDs, Reality private keys, API tokens, SSH private keys, or production inventories**.
- GitHub repository may be public. Use Ansible Vault or an external secret manager for secrets; do not include them in examples or issue reports.

### Roadmap

- Verified read-only discovery of NGINX, Xray and 3x-ui state
- Encrypted, restorable snapshots with checksums and documented recovery procedures
- Idempotent provisioning for *fresh* VPS with staged validations
- Explicit opt-in 3x-ui-compatible configuration lifecycle (SQLite/API ownership)
- Observable health/failover checks; no disruptive failover simulation on production
- Unit tests / integration tests on disposable VMs

## Русский

`vpnctl` — компактная двуязычная консоль для Ansible. Первая версия позволяет проверять SSH-доступность серверов, состояние служб, создавать локальные резервные копии и публиковать статический сайт. **Это ещё не полноценная автоматическая установка VPN.**

### Подготовка

Для Windows используйте WSL. Необходимы Python 3.10+, SSH, rsync и Ansible. Укажите собственные адреса и SSH-доступ в `inventory/local.yml` (файл исключён из Git).

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yml
cp inventory/hosts.yml inventory/local.yml
# отредактируйте inventory/local.yml
python3 vpnctl.py --lang ru --inventory inventory/local.yml hosts
python3 vpnctl.py --lang ru --inventory inventory/local.yml ping --host fi_in_2
python3 vpnctl.py --lang ru --inventory inventory/local.yml status --host fi_in_2
python3 vpnctl.py --lang ru --inventory inventory/local.yml discover --host fi_in_2
python3 vpnctl.py --lang ru --inventory inventory/local.yml backup --host fi_in_2 --apply
python3 vpnctl.py --lang ru --inventory inventory/local.yml clock --host fi_in_2 --check
python3 vpnctl.py --lang ru --inventory inventory/local.yml clock --host fi_in_2 --apply
```

Команды `ping`, `status` и `discover` ничего не меняют. `discover` сообщает состояние сервисов и прослушиваемые TCP-порты, но не проверяет работу VPN-маршрута. `backup` сохраняет **чувствительные данные** в локальной папке `backups/`; храните резервные копии зашифрованными и не выкладывайте в GitHub. Для `backup` нужен `rsync` и соответствующие права на удалённом сервере; сначала протестируйте на тестовом VPS. `clock --apply` только копирует файлы сайта в `/var/www/adelaide-clock`, **не меняет NGINX и VPN**. Рабочий NGINX пока требуется подключать вручную после проверки существующего `server`-блока.

Для новой инфраструктуры используйте тестовый VPS. Никогда не публикуйте приватные ключи REALITY, пароли панелей, секреты, UUID клиентов и реальные файлы конфигурации. Следующий этап — безопасная автоматизация полной установки с 3x-ui/Xray, снапшотами и проверками переключения.

## CI / Автоматические проверки

GitHub Actions validates Python unit tests and Ansible syntax on pushes/PRs. The workflow does **not** connect to VPS instances or read production credentials.

GitHub Actions проверяет тесты Python и синтаксис Ansible при коммитах и pull request. Workflow **не подключается** к VPS и не использует рабочие секреты.


## v0.3: Fresh VPS bootstrap / Подготовка тестового VPS

**EN:** Read [Fresh VPS bootstrap](docs/bootstrap.en.md). A guarded, opt-in `bootstrap` command installs NGINX on a disposable host, with optional standalone Xray from a SHA-256 verified release and private JSON config. No 3x-ui, no REALITY setup, no failover yet.

**RU:** См. [инструкцию подготовки тестового VPS](docs/bootstrap.ru.md). Команда `bootstrap` с дополнительными подтверждениями устанавливает NGINX на новом тестовом сервере и, по желанию, отдельный Xray из проверенного SHA-256 архива. Конфигурация 3x-ui, REALITY и резервирование пока не автоматизированы.

## v0.4 — offline topology configuration / Генерация топологии

The `render` command generates example Xray and NGINX Stream configuration files for `entry`, `relay`, and `exit` nodes, without connecting to any VPS. **No automatic deployment and no 3x-ui modification.** See [English guide](docs/topology.en.md).

Команда `render` локально генерирует конфигурации Xray и фрагменты NGINX Stream для узлов `entry`, `relay` и `exit`, без доступа к VPS. **Автоматического развёртывания и изменения 3x-ui пока нет.** См. [русскую инструкцию](docs/topology.ru.md).

```bash
cp examples/topology.example.json topology.local.json
# Replace intentionally invalid X25519 key placeholders and other sample values
python3 vpnctl.py --lang ru render --topology topology.local.json --output rendered
```

---

## v1.0 development bundle / Сборка v1.0 для разработки

This release combines a bilingual Ansible CLI, local topology generator, local
prerequisite checks, credentials generation, offline validation and planning,
read-only remote diagnostics, opt-in fresh test VPS bootstrap and *non-activating*
configuration staging. It is **not** a production-ready fully automatic VPN installer.

Сборка объединяет двуязычную консоль, генератор топологий, проверку окружения,
генерацию учётных параметров, локальную валидацию, диагностику серверов,
подготовку отдельного тестового VPS и передачу конфигураций **без активации**.
Это **не готовый промышленный установщик VPN «в один клик»**.

- [English quick start](docs/quickstart.en.md)
- [Русская инструкция](docs/quickstart.ru.md)

Quick commands / Команды:

```bash
python3 vpnctl.py --lang ru doctor
python3 vpnctl.py --lang en keys
python3 vpnctl.py --lang ru validate --topology topology.local.json
python3 vpnctl.py --lang en plan --topology topology.local.json
python3 vpnctl.py --lang ru render --topology topology.local.json --output rendered
python3 -m unittest discover -s tests -v
```

**Security:** Never publish private inventory, Reality secrets, server credentials,
SSH keys or generated bundles. The project does not connect to production systems
without a user-invoked Ansible command. Review playbooks before use.

## Experimental staged activation / Экспериментальная активация

A fresh, expressly authorized **disposable test VPS** can use `activate` to promote an already-staged standalone Xray JSON after backup and syntax validation. The action is separated from `bootstrap` and `stage`, requires a single host and interactive `APPLY`, and attempts rollback if Xray restart or loopback listener check fails. It does **not** configure NGINX Stream, HTTPS certificates, DNS, or test an end-to-end VPN route. This feature is unverified on a real VPS. See [RU](docs/quickstart.ru.md) / [EN](docs/quickstart.en.md).

На отдельном **тестовом VPS** команда `activate` сохраняет исходную конфигурацию, проверяет кандидата и перезапускает только самостоятельный Xray. При обнаруженной ошибке выполняется попытка отката. DNS, NGINX Stream, HTTPS и проверка VPN-маршрута остаются отдельными операциями. На реальном VPS процедура пока не испытана.
