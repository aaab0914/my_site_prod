# Middleware Migration Plan

## Goal

Reduce the global path allowlist in `LoginRequiredMiddleware` and move access control to view-level decorators where possible.

## Move First

These routes are best moved out of middleware gating first:

- `/blog/feed/`
- `/blog/search/`
- `/blog/tag/<slug>/`
- `/blog/<detail>/` if you want public detail pages

Reason:

- They are public or mostly public content routes.
- Path-based gating is easy to break when URLs change.

## Keep In Middleware For Now

These routes can stay gated while the migration is in progress:

- `/blog/create/`
- `/blog/audio/upload/`
- `/users/profile/`
- `/users/profile/<username>/`
- `/users/profile_edit/`
- `/users/account/delete/`
- `/users/username/change/`

Reason:

- They are user actions that naturally require authentication.
- They are lower risk to keep protected during transition.

## Admin

- Leave `/admin/` to Django's admin auth system.

## Suggested End State

- Public views:
  - no middleware dependency
  - explicit route behavior
- Private views:
  - use `@login_required`
  - add object-level permission checks where needed
- Middleware:
  - keep for logging, audit, and non-business cross-cutting concerns

## Safe Migration Order

1. Remove public content routes from the allowlist only if you later decide they should be private.
2. Add tests for public access to those routes.
3. Convert private user actions to explicit decorators.
4. Reduce the middleware allowlist to only the unavoidable cases.
