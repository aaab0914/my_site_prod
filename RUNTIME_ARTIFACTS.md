# Runtime Artifacts

This project keeps source code separate from runtime-generated data.

The following root directories are runtime artifacts and should not be committed:
- `data/`
- `media/`
- `staticfiles/`
- `logs/`
- `backups/`

Usage guidance:
- `data/` stores local database container state.
- `media/` stores uploaded user content.
- `staticfiles/` stores collected static assets.
- `logs/` stores application and infrastructure logs.
- `backups/` stores database and media backups.

Keep these directories outside code review focus. Treat them as environment state, not source files.
