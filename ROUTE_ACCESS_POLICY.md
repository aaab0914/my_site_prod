# Route Access Policy

## Public

- `/blog/`
- `/blog/audio/list/`
- `/blog/feed/`
- `/blog/search/`
- `/users/login/`
- `/users/register/`
- RSS feeds
- sitemap
- static assets

## Login Required

- `/blog/create/`
- `/blog/audio/upload/`
- `/blog/<detail>/` if kept private
- edit / delete routes
- profile / account management
- user settings

## Admin Only

- `/admin/`

## Suggested Rule

- Use `@login_required` on private views.
- Keep public routes explicit.
- Avoid broad path-based login gating in middleware.
- If middleware is kept, only use it for a small allowlist of truly public routes.
- Tagged blog routes may need prefix matching in middleware if you keep path-based gating.
