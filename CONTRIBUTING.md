# Contributing

Thanks for your interest in doctor-Agent.

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Checks Before Opening A PR

```bash
cd backend
python -m pytest -q
```

```bash
cd frontend
npm run build
```

## Medical Safety

Changes that affect answers must preserve these rules:

- Do not claim to diagnose disease.
- Do not prescribe medication or dosage.
- Keep emergency symptoms routed to urgent care guidance.
- Keep the medical disclaimer visible in user-facing responses.
- Prefer deterministic tests for high-risk and medication-safety cases.

## Secrets

Never commit `.env`, API keys, Dify credentials, tunnel URLs, local SQLite databases, logs, or generated reports.
