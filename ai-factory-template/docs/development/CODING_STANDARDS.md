# Coding Standards — <PROJECT-NAME>

This document defines the coding conventions, patterns, and best practices used
in this project. Follow these standards when writing or modifying code to
maintain consistency.

> Agents reference sections as `STANDARDS §<n>`; keep the `##` numbering
> stable when editing.

---

## 1. General Principles

<!-- INIT: e.g. consistency over preference; explicit over implicit; fail
     fast; security first; document intent. -->

- **Consistency over preference** — Follow existing patterns in the codebase.
- **Explicit over implicit** — Use type hints, explicit imports, and clear naming.
- **Fail fast** — Validate early, raise descriptive errors, log failures.
- **Security first** — Never commit secrets; validate inputs; use parameterized queries.
- **Document intent** — Docstrings for modules, classes, and public functions.

---

## 2. Backend (<language / framework>)

<!-- INIT: version & tooling, project structure, naming, imports, type rules,
     error handling, logging, lint/format commands. One `### 2.x` subsection
     per topic — the `Context:` line mechanism references these. -->

### 2.1 Version & Tooling

### 2.2 Project Structure

### 2.3 Naming Conventions

### 2.4 Imports

### 2.5 Error Handling & Logging

### 2.6 Lint / Format

---

## 3. Frontend (<language / framework>)

<!-- INIT: component conventions, state management, styling approach, API
     call layer, testing rules. Delete if backend-only. -->

### 3.1 Components

### 3.2 API Calls

### 3.3 Styling

---

## 4. Database

<!-- INIT: model conventions, migration rules, query patterns. Delete if no
     database. -->

---

## 5. Testing & Mocking

<!-- INIT: test harness locations, the mock seams for every external system,
     and the non-negotiable rule that tests never make real external calls. -->

---

## 6. Security Rules

<!-- INIT: auth dependency usage, input validation, secrets, SQL safety. -->
