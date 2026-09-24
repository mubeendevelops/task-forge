# TaskForge Demo Guide

## Part 1: Demo Script (5–7 min)

**Before you start:** open a terminal in the project folder and run `./setup.sh` (Windows: `.\setup.ps1`).
Wait until it prints the URLs. Keep these tabs open: App, Prometheus, Grafana, Alertmanager.

### A. The app (1 min)
1. Open http://localhost:5000.
   *Say: "TaskForge is a Flask to-do app with in-memory storage."*
2. Type `Buy milk`, click **Add task**. Add a second task.
   *Say: "The page calls `POST /api/tasks` with fetch, no reload."*
3. Tick the checkbox on one task, then click **Delete** on the other.
   *Say: "Ticking calls `PATCH /api/tasks/<id>`, Delete calls `DELETE`."*
4. Click the **Active** and **Done** tabs.
   *Say: "The tabs filter in the browser; the counter shows tasks remaining."*
5. Open http://localhost:5000/metrics.
   *Say: "This is what Prometheus reads: our three custom metrics."*

### B. Prometheus (1 min)
1. Open http://localhost:9090/targets → job `taskforge` shows **UP**.
   *Say: "Prometheus scrapes `app:5000/metrics` every 5 seconds."*
2. Open http://localhost:9090/graph and run each query:
   - `sum(rate(app_http_requests_total[1m]))` — requests per second.
   - `histogram_quantile(0.95, sum by (le) (rate(app_http_request_duration_seconds_bucket[1m])))` — 95% of requests are faster than this.
   - `sum(rate(app_http_errors_total[1m])) / sum(rate(app_http_requests_total[1m]))` — share of requests that failed with 5xx.

### C. Grafana + load test (2 min)
1. Open http://localhost:3000 → **Dashboards** → **TaskForge**. (Already there: it is provisioned; login is `admin` / `admin` if asked.)
   *Say: "Nobody clicked to create this. It loads from files in `grafana/`."*
2. In a terminal run: `python3 scripts/load_test.py --duration 120`
   *Say: "This sends mixed traffic, including some `/error` calls."*
3. Point at each panel (refreshes every 5s):
   - **Request rate (req/s)**: lines jump up per endpoint.
   - **p95 latency**: shows how slow the slowest 5% are.
   - **Error rate (5xx / total)**: rises above zero.
   - **Total requests**: keeps counting up.

### D. HighErrorRate alert (1 min)
1. Run more errors so the rate stays clearly above 10%:
   `python3 scripts/load_test.py --duration 120 --error-rate 0.4`
2. After about 1–2 minutes open http://localhost:9090/alerts → **HighErrorRate** goes Pending, then **Firing**.
   *Say: "The rule fires when more than 10% of requests are 5xx."*
3. Open http://localhost:9093 → the same alert appears.
   *Say: "Prometheus sends it to Alertmanager, which groups and routes it."*

### E. AppDown alert (1 min)
1. Run: `docker compose stop app`
2. Wait ~30 seconds. Check http://localhost:9090/targets (DOWN) and http://localhost:9090/alerts (**AppDown** firing).
   *Say: "`up == 0` means Prometheus can't reach the app."*
3. Run: `docker compose start app` → the alert clears after the next scrape.

### F. GitHub Actions (30 sec)
This folder is not a Git repo yet. One-time setup: create an empty GitHub repo, then run
`git init && git add . && git commit -m "TaskForge" && git branch -M main && git remote add origin <your-repo-url> && git push -u origin main`.
1. Open your repo on GitHub → **Actions** tab → latest **CI** run.
   *Say: "On every push it runs flake8, pytest, docker build and `docker compose config`."*

Cleanup: `docker compose down`

---

## Part 2: Viva Concepts

### DevOps
- **What:** Practices that connect writing code with running it: automate build, test, deploy and monitoring. Like a factory line instead of hand-crafting.
- **How we used it:** whole project. Automation in `setup.sh`, `.github/workflows/ci.yml`; monitoring in `prometheus/`, `grafana/`.

### Docker
- **What:** Packages an app and everything it needs into an image that runs the same everywhere. Like a lunchbox with the meal inside.
- **How we used it:** `Dockerfile` (multi-stage, non-root user `appuser`, `HEALTHCHECK` on `/health`, gunicorn on port 5000).

### Docker Compose
- **What:** Starts several containers together from one file. Like one order for a whole meal.
- **How we used it:** `docker-compose.yml` runs app, prometheus, grafana and alertmanager with pinned image versions.

### Prometheus
- **What:** A database that collects numbers over time and can raise alerts. Like a fitness tracker for servers.
- **How we used it:** `prometheus/prometheus.yml` (scrape job `taskforge`), `prometheus/alerts.yml` (rules).

### Metrics and scraping
- **What:** A metric is a number the app exposes; scraping means Prometheus fetches it on a timer (pull model).
- **How we used it:** `app/app.py` defines `app_http_requests_total`, `app_http_request_duration_seconds` and `app_http_errors_total`, served at `/metrics`.

### PromQL
- **What:** Prometheus's query language, e.g. `rate()` turns an ever-growing counter into "per second".
- **How we used it:** `prometheus/alerts.yml` and the panel queries in `grafana/dashboards/taskforge.json`.

### Grafana
- **What:** Turns Prometheus data into graphs on a dashboard.
- **How we used it:** `grafana/dashboards/taskforge.json`: request rate, p95 latency, error rate, total requests.

### Provisioning
- **What:** Configuring a tool from files at startup instead of clicking in the UI, so setup is repeatable.
- **How we used it:** `grafana/provisioning/datasources/prometheus.yml` and `grafana/provisioning/dashboards/dashboards.yml`.

### Alertmanager
- **What:** Receives alerts from Prometheus, groups them and decides where they go. Like a dispatcher.
- **How we used it:** `alertmanager/alertmanager.yml` (demo setup, alerts are shown in its UI, no email/Slack).

### CI / GitHub Actions
- **What:** CI automatically builds and tests every change. GitHub Actions runs it on GitHub's servers.
- **How we used it:** `.github/workflows/ci.yml` on push and pull request.

### YAML
- **What:** A readable indentation-based format for configuration.
- **How we used it:** `docker-compose.yml`, `prometheus/*.yml`, `alertmanager/alertmanager.yml`, `ci.yml`, Grafana provisioning files.

### Bash / PowerShell scripting
- **What:** Command-line scripts that automate repeated steps.
- **How we used it:** `setup.sh` and `setup.ps1` check Docker, run `docker compose up -d --build`, wait for `/health`, print URLs.

### Python automation
- **What:** Using Python to do jobs for us, like tests and traffic generation.
- **How we used it:** `scripts/load_test.py` (standard library only) and `tests/test_app.py` (pytest).

### Likely viva questions
1. **Why Docker?** Same environment on every machine; only Docker is needed to run the project.
2. **Image vs container?** An image is the recipe/package; a container is a running copy of it.
3. **Why a multi-stage Dockerfile?** Build tools stay in the first stage, so the final image is smaller.
4. **Why run as non-root?** If the app is compromised, the attacker has fewer privileges.
5. **Pull vs push monitoring?** Prometheus pulls (scrapes) `/metrics`; the app doesn't send data.
6. **Why `rate()` on a counter?** A counter only goes up; `rate()` shows how fast it grows per second.
7. **How does HighErrorRate work?** 5xx requests divided by all requests over 1 minute, above 10%, for 15 seconds.
8. **Prometheus vs Alertmanager?** Prometheus decides when an alert fires; Alertmanager handles what happens next.
9. **Why provision Grafana?** The dashboard and datasource appear automatically, with no manual clicking.
10. **What does CI do here?** flake8 (style), pytest (tests), `docker build`, `docker compose config` on every push.
