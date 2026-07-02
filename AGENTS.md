# Repository Guidelines

## Project Structure & Module Organization
This repository is an npm workspace for CS Job Radar. The main web app lives in `apps/web` and uses Next.js, React, TypeScript, Tailwind CSS, and ESLint. Shared packages are under `packages/`: `db` contains migrations, `config` holds shared configuration, and `shared` is for cross-app utilities. Data-processing and automation code lives in `scripts` and `services`; crawler, analyzer, and reporter concerns are split under `services/crawler`, `services/analyzer`, and `services/reporter`. Curated dictionaries and source metadata are stored in `data`.

## Build, Test, and Development Commands
Run commands from the repository root unless noted otherwise.

- `npm install`: install workspace dependencies.
- `npm run dev`: start the Next.js development server for `apps/web`.
- `npm run build`: build the web app for production.
- `npm run lint`: run ESLint for the web app.
- `python scripts/init_db.py`: initialize the database schema.
- `python scripts/run_pipeline.py`: run the local crawl, normalize, and reporting pipeline.

Copy `.env.example` to `.env` and set `DATABASE_URL` before running database-backed code.

## Coding Style & Naming Conventions
Use TypeScript for web code and keep `strict` compiler settings clean. Prefer the `@/*` alias inside `apps/web` for local imports. Components should use PascalCase (`Topbar.tsx`), hooks and helpers should use camelCase, and route folders should follow Next.js conventions such as `app/cities/[city]/page.tsx`. Python modules should use snake_case and keep crawler, parser, classifier, and reporting logic in their existing service folders.

## Testing Guidelines
No formal test framework is currently configured. For now, validate changes with `npm run lint`, `npm run build`, and targeted script runs such as `python scripts/verify_sources.py`. When adding tests, colocate web tests near the feature or use a clear `tests` directory, name files `*.test.ts(x)` or `test_*.py`, and document any new runner in `package.json` or service requirements.

## Commit & Pull Request Guidelines
Project history currently uses conventional-style messages such as `feat: ...`, `fix: ...`, `perf: ...`, and `debug: ...`. For this repository, prefer branch names `feat-xxx` or `fix-xxx` and commit messages `[feat] xxx` or `[fix] xxx`. Pull requests should include a concise summary, validation steps, linked issues when available, and screenshots for UI changes.

## Agent-Specific Instructions
For `apps/web`, read `apps/web/AGENTS.md` before editing; it notes that this Next.js version has breaking changes and local documentation in `node_modules/next/dist/docs/` should be checked before framework-level changes.
