# RealTime Vehicle Tracking System

![Project Banner](public/og-image.png)

A modern web application starter ready for building a Vehicle Detection & Counting dashboard. Built with Vite, React, TypeScript, Tailwind CSS, and shadcn/ui — focusing on developer ergonomics, performance, and clean UI primitives.

---

## ✨ Features
- Fast dev experience with `vite` and `react-swc`
- Type-safe codebase with `TypeScript`
- Utility-first styling via `Tailwind CSS`
- Polished UI using `shadcn/ui` (Radix UI under the hood)
- State and data fetching with `@tanstack/react-query`
- Routing with `react-router-dom`
- Sensible linting via `eslint` and React Hooks rules

---

## 🧠 Tech Stack
- React + TypeScript
- Vite (SWC) on port `8080`
- Tailwind CSS + `tailwind-merge` + `clsx`
- shadcn/ui components (Radix UI)
- React Query for server state
- ESLint (typescript-eslint, react-hooks, react-refresh)

---

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start dev server (http://localhost:8080)
npm run dev

# Lint the project
npm run lint

# Build for production
npm run build

# Preview the production build
npm run preview
```

---

## 📁 Project Structure

```text
.
├─ public/
│  ├─ favicon.ico
│  └─ og-image.png
├─ src/
│  ├─ components/ui/      # shadcn/ui primitives (do not modify directly)
│  ├─ hooks/              # custom hooks (e.g., mobile, toast)
│  ├─ pages/              # route-level pages
│  ├─ lib/                # utilities (e.g., classnames)
│  ├─ App.tsx             # app shell (router, providers)
│  ├─ main.tsx            # app entry
│  └─ index.css           # tailwind and theme tokens
├─ index.html             # vite entry
├─ tailwind.config.ts     # tailwind setup
├─ vite.config.ts         # dev server & aliases
└─ eslint.config.js       # lint rules
```

---

## 🎨 Styling
- Design tokens are defined in `src/index.css` and consumed via Tailwind classes
- Tailwind config lives in `tailwind.config.ts` (dark mode supported)
- Use `cn()` from `src/lib/utils.ts` to merge class names safely

---

## 🧩 UI Components
- Uses `shadcn/ui` for accessible, composable components
- Radix primitives are already wired up; prefer composition over heavy customization
- Toasts, tooltips, dialogs, forms, and more are available under `src/components/ui/`

---

## 🗺️ Routing & State
- `react-router-dom` powers routing; the root route is `src/pages/Index.tsx`
- `@tanstack/react-query` manages server state; the provider is initialized in `App.tsx`

---

## 🔧 Development Notes
- Dev server runs on `http://localhost:8080`
- Avoid editing files listed under "Forbidden files" if present; treat UI components as library code
- Prefer small, focused components and clear state boundaries

---

## 📸 Screenshots
Use `public/og-image.png` or add your own screenshots to showcase the UI.

---

## 🤝 Contributing
- Keep components small (< 50 lines when feasible)
- Add logs and user-friendly feedback for error handling
- Write unit tests for critical logic

---

## 📜 License
No license specified. Add your preferred license file.

---

## 📣 Acknowledgements
- [Vite](https://vitejs.dev/)
- [React](https://react.dev/)
- [TypeScript](https://www.typescriptlang.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [shadcn/ui](https://ui.shadcn.com/)
- [Radix UI](https://www.radix-ui.com/)
- [TanStack Query](https://tanstack.com/query/latest)
