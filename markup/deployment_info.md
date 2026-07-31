# GuardAI - Important Links & Deployment Info

This document contains all the necessary links, credentials, and commands needed to manage the GuardAI Intelligent Action Governance Platform.

## 🔗 Live URLs
- **Production Dashboard:** [http://51.21.171.205:3000](http://51.21.171.205:3000)
- **Backend API (Swagger Docs):** [http://51.21.171.205:8000/docs](http://51.21.171.205:8000/docs)
- **Backend API (Redoc):** [http://51.21.171.205:8000/redoc](http://51.21.171.205:8000/redoc)
- **Backend Health Check:** [http://51.21.171.205:8000/health](http://51.21.171.205:8000/health)

## 🖥️ Server Access (AWS EC2)
To access the production server, open your Mac terminal and run:
```bash
ssh -i ~/Downloads/guardai-key.pem ubuntu@51.21.171.205
```

## 🛠️ Useful Docker Commands
If you ever need to restart or manage the application on the AWS server, use these commands (run them from inside the `GuardAI-Intelligent-Action-Governance-Platform` folder on the server):

- **View Live Logs (All services):** `docker compose logs -f`
- **View Live Logs (Frontend only):** `docker compose logs -f web`
- **Restart the Platform:** `docker compose restart`
- **Stop the Platform:** `docker compose down`
- **Start/Rebuild the Platform:** `docker compose up -d --build`
- **Clean up Disk Space:** `docker system prune -a -f`

## 🔑 Pre-Seeded Test Accounts
The database automatically seeds these accounts on boot so you can immediately test Role-Based Access Control (RBAC):

| Username | Password | Role |
| :--- | :--- | :--- |
| `admin` | `Password123!` | `ADMIN` |
| `manager_jane` | `Password123!` | `MANAGER` |
| `dev_alex` | `Password123!` | `EMPLOYEE` |
| `auditor_bob` | `Password123!` | `AUDITOR` |
