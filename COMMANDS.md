# Commands

Useful commands for local development and common fixes.

Run commands from the repo root:

```powershell
cd e:\Code_Projects\pnf
```

## Activate Environment

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Or run Python directly from the venv:

```powershell
.\.venv\Scripts\python.exe -m trading_app.cli show-config
```

## App CLI

Show current redacted config:

```powershell
python -m trading_app.cli show-config
```

Direct file mode also works, but you must pass a command:

```powershell
python trading_app\cli.py show-config
python trading_app\cli.py health
```

If you run only this:

```powershell
python trading_app\cli.py
```

you will see:

```text
the following arguments are required: command
```

That is expected. Use `show-config` or `health`.

## QuestDB

Start QuestDB:

```powershell
docker compose up -d questdb
```

Stop QuestDB but keep data:

```powershell
docker compose stop questdb
```

Stop and remove container but keep data volume:

```powershell
docker compose down
```

Open QuestDB Web Console:

```text
http://localhost:19000
```

Health check:

```powershell
python -m trading_app.cli health
```

Expected when running:

```text
questdb ok: HTTP 200
```

Expected when stopped:

```text
questdb failed
```

## QuestDB Ports

This project uses conflict-safe host ports:

```text
Web Console:   localhost:19000
ILP:           localhost:19009
Postgres wire: localhost:18812
```

QuestDB internal container ports remain:

```text
9000, 9009, 8812
```

If another app uses one of this project's host ports, change `.env`:

```text
QUESTDB_HTTP_PORT=19000
QUESTDB_ILP_PORT=19009
QUESTDB_PG_PORT=18812
```

Then restart:

```powershell
docker compose up -d questdb
```

See running containers and ports:

```powershell
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

## Fix: Port Already Allocated

Error example:

```text
Bind for 0.0.0.0:9000 failed: port is already allocated
```

Check what is using Docker ports:

```powershell
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

Do not stop unrelated containers unless you know they are safe to stop.

Preferred fix for this project: use the configured host ports:

```text
19000, 19009, 18812
```

Then run:

```powershell
docker compose up -d questdb
```

## Fix: vm.max_map_count Warning

Warning:

```text
vm.max_map_count limit is too low [current=262144, recommended=1048576]
```

Fix for Docker Desktop WSL VM:

```powershell
wsl -d docker-desktop -u root sysctl -w vm.max_map_count=1048576
```

Verify:

```powershell
wsl -d docker-desktop -u root cat /proc/sys/vm/max_map_count
```

Expected:

```text
1048576
```

Then restart QuestDB:

```powershell
docker compose restart questdb
```

This setting may reset after Docker Desktop or WSL restarts.

## Fix: QuestDB Instance Name Is Not Set

Check settings:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:19000/settings | Select-Object -ExpandProperty Content
```

Set instance metadata:

```powershell
$body = @{
  instance_name = "PnF Trading Platform"
  instance_type = "development"
  instance_description = "Local QuestDB for PnF trading platform"
  instance_rgb = "g"
} | ConvertTo-Json -Depth 5

Invoke-WebRequest `
  -UseBasicParsing `
  -Method Put `
  -Uri "http://localhost:19000/settings?version=0" `
  -ContentType "application/json" `
  -Body $body
```

If QuestDB says preferences are out of date, get the latest version:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:19000/settings | Select-Object -ExpandProperty Content
```

Then replace `version=0` with the current `preferences.version`.

Refresh browser:

```text
Ctrl + F5
```

## Tests And Checks

Compile:

```powershell
python -m compileall pnf tests trading_app
```

Run all tests:

```powershell
python -m pytest -q
```

If system Python has no pytest, use venv Python:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run only app foundation tests:

```powershell
python -m pytest -q tests\test_app_config.py tests\test_app_health.py
```

## Git

Check status:

```powershell
git status --short
```

After `git init`, all existing files may show as untracked until the first commit.

## Daily Workflow

Start:

```powershell
cd e:\Code_Projects\pnf
.\.venv\Scripts\Activate.ps1
docker compose up -d questdb
python -m trading_app.cli health
```

Stop:

```powershell
docker compose stop questdb
```
