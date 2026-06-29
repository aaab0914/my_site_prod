# Route Access Audit

## Blog

- `/blog/` -> public, matches policy
- `/blog/audio/list/` -> public, matches policy
- `/blog/create/` -> login required, matches policy
- `/blog/audio/upload/` -> login required, matches policy
- `/blog/<detail>/` -> currently login gated by middleware, policy says choose explicitly
- `/blog/feed/` -> public, now aligned with policy
- `/blog/search/` -> public, now aligned with policy
- `/blog/tag/<slug>/` -> public, matches policy

## Users

- `/users/login/` -> public, matches policy
- `/users/register/` -> public, matches policy
- `/users/profile/` -> currently login gated, matches policy
- `/users/profile/<username>/` -> currently login gated, matches policy
- `/users/profile_edit/` -> login required, matches policy
- `/users/account/delete/` -> login required, matches policy
- `/users/username/change/` -> login required, matches policy
- `/users/logout/` -> login required, acceptable

## Admin

- `/admin/` -> admin only, matches policy

## Gaps

- The middleware is still the main access-control gate for private blog and user routes.
- Public content routes now match the policy; route-by-route decorators are still the better long-term direction for private views.
