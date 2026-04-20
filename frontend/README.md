# Frontend Directory

This directory contains the frontend foundation for the robotic arm control agent web console.

## Current Scope

Step 04 only establishes the frontend project baseline:

- Node.js + React 19 + TypeScript + Vite 8 + Ant Design
- application shell and route framework
- page, component, API, and state-management directory boundaries
- naming rules for routes, pages, and stores
- placeholder pages for future feature areas

No business data flow, authentication flow, or backend integration is implemented in this step.

## Directory Layout

- `public/`: static assets reserved for the console
- `src/app/`: app composition, providers, and route metadata
- `src/routes/`: router definition and route tree
- `src/pages/`: page-level components only
- `src/components/`: reusable UI pieces shared across pages
- `src/api/`: HTTP client setup and API modules
- `src/stores/`: UI and session state containers
- `src/styles/`: global tokens and layout styles

## Naming Conventions

- Route path segments use `kebab-case`
  - example: `/tasks/new`, `/knowledge/items`, `/config/safety-rules`
- Page files use `kebab-case` and the suffix `.page.tsx`
  - example: `task-list.page.tsx`, `alert-center.page.tsx`
- Reusable components use `kebab-case`
  - example: `console-shell.tsx`, `feature-placeholder.tsx`
- Store files use `kebab-case` and the suffix `.store.tsx`
  - example: `app-shell.store.tsx`
- API modules use `kebab-case` and the suffix `.api.ts`
  - example: `system.api.ts`

## Route Framework

Current route skeleton reserves space for:

- `/login`
- `/tasks`
- `/tasks/new`
- `/tasks/:taskId`
- `/alerts`
- `/audit`
- `/knowledge/items`
- `/knowledge/samples`
- `/config/robot`
- `/config/safety-rules`

These are placeholder pages only, used to prove the route structure and information architecture.

## Commands

Install dependencies:

```powershell
npm.cmd install
```

Start the local development server:

```powershell
npm.cmd run dev
```

Build for verification:

```powershell
npm.cmd run build
```

## Environment Convention

- Frontend environment variables use the `VITE_` prefix
- `VITE_API_BASE_URL` is reserved for future backend integration
- This step does not require a live backend service
