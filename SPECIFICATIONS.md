# Cookbook App — Specifications

## Overview

A self-hosted web application for creating, managing, and iteratively improving cooking recipes. The core value is **version-controlled recipes**: every saved change creates an immutable version with a rating, enabling the user to track improvements over time (e.g., "added 10% more salt → rated 4/5 stars").

---

## Architecture

### High-Level Stack
| Layer | Technology |
|---|---|
| Frontend | Vue 3 SPA |
| Backend | Python / FastAPI (REST API) |
| Database | SQLite via SQLAlchemy ORM (swappable to PostgreSQL) |
| Version Control | Git repo managed by the app, pushed to GitHub |
| Deployment | Docker on home NAS, exposed via Cloudflare Tunnel |

### Data Storage Strategy
- **Git repo** stores recipe content as YAML files (one file per recipe), enabling human-readable diffs and full history via GitHub.
- **Database** stores metadata for fast search/filtering: categories, tags, ratings, users, draft state, sharing flags.
- On every "Save Version", the app writes the YAML, commits to the local git repo, and pushes to GitHub.
- **Each user connects their own GitHub repo** (public or private — their choice) via a personal access token. The app manages commits and pushes autonomously.
- Repo structure per user: `recipes/{recipe-slug}.yaml` within their own repository.

---

## Recipe Structure

Each recipe is stored as a YAML file. All quantities use the **metric system** (g, ml, cm, °C, etc.).

```yaml
title: "Pasta al Pomodoro"
description: "Classic Italian tomato pasta"
servings: 4
prep_time: 10       # minutes
cook_time: 20       # minutes
categories: [Italian, Pasta]
tags: [vegetarian, quick]
notes: ""
photos: []

ingredients:
  - name: Pasta
    quantity: 200
    unit: g
  - name: Tomato sauce
    quantity: 300
    unit: ml
  - name: Salt
    quantity: 5
    unit: g

preparations:
  - "Bring a large pot of water to a boil"

steps:
  - "Add salt to the boiling water"
  - "Cook pasta for 8 minutes until al dente"
  - "Heat tomato sauce in a pan for 5 minutes"
  - "Drain pasta and combine with sauce"
```

The YAML structure is intentionally flexible — additional metadata fields can be added without breaking the schema.

---

## Version Control Logic

### Draft State
- A recipe with uncommitted local changes is in **draft** state.
- Drafts persist across sessions (saved to the database, not yet committed to git).
- Users can accumulate edits over multiple days/sessions before saving a version.
- A visible indicator marks a recipe as "unsaved changes".

### Saving a Version
- The user explicitly triggers **"Save Version"** (analogous to `git commit`).
- The user assigns a **1–5 star rating** at save time.
- Once saved, a version is **immutable**.
- The app commits the YAML to the git repo and pushes to GitHub.

### Tweaking Ingredients
- Each ingredient has **+** and **−** buttons that adjust quantity by a configurable step (default: **10%**, settable in app config).
- Quantities can also be **free-typed** directly.
- Changes accumulate in draft state until the user saves a version.

### Version Diff
- Users can compare any two versions of a recipe side-by-side.
- Diffs highlight: ingredient quantity/unit changes, added/removed ingredients, and changes to steps.

---

## Features

### MVP (Core)
- Create, edit, delete recipes
- Draft state with persistent unsaved changes
- Save Version → git commit + push to GitHub
- 1–5 star rating per version
- Ingredient tweaking (% buttons + free-type)
- Side-by-side version diff viewer
- Organize by categories (primary) and tags (secondary)
- Full-text search
- Multi-user authentication (login/register)
- App config section (tweak %, GitHub token, etc.)
- Docker deployment with Cloudflare Tunnel support

### Future / Plugin Ideas
- Meal planner: assign recipes to days of the week
- Shopping list generator: aggregate ingredients from a meal plan
- Recipe import from URL (web scraping)
- Nutritional information per recipe

---

## User & Auth Model

- **Multi-user**: the app supports multiple users, designed to be SaaS-compatible.
- **Authentication required**: all access requires login (username + password).
- **Write access is per-user**: users can only create, edit, or delete their own recipes.

### Recipe Sharing
- Recipes have a `shared` flag (default: **private**).
- **Private** recipes are only visible to their owner within the app.
- **Shared** recipes are visible to all authenticated users in a "Shared Recipes" section.
- Any user can **fork** a shared recipe into their own cookbook — creating an independent copy in their own repo, with attribution (e.g., `forked from @alice/pasta-al-pomodoro`).
- A forked recipe has its own independent version history and ratings.

### GitHub Connection (per user)
- Each user configures their own GitHub repo and personal access token in their profile settings.
- The app commits and pushes to each user's repo autonomously — no manual git interaction required.
- Users choose whether their GitHub repo is public or private; this is independent of the app's `shared` flag.

---

## Infrastructure & Deployment

- **Docker**: single `docker-compose` setup (app + SQLite volume).
- **Networking**: bridge mode with a static LAN IP address.
- **External access**: Cloudflare Tunnel → custom subdomain.
- **GitHub integration**: the app manages each user's git repo autonomously (commit, push). No manual git interaction required.

### App Configuration (settable via UI)
- Ingredient tweak step percentage (default: 10%)
- Per-user: GitHub repository URL and personal access token
- Other app-wide settings

---

## Out of Scope (for now)
- Recipe import from external URLs
- Nutritional information
- Native mobile app (responsive web is sufficient)
- Self-hosted git server (e.g. Gitea) — GitHub only for now
