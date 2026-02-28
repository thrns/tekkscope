# Kubernetes deployment notes

The backend deployment expects a `dockerhub-secret` image-pull secret and the
application secrets used by `backend/.env.example`. Create those through the
cluster secret manager; do not commit a populated Secret manifest.

Apply the SQL files in `backend/migrations/` to the Supabase project before
creating production API keys. The application has compatibility fallbacks for
older schemas, but the richer security and usage metadata requires the
migrations.

The CD workflow applies the backend and Redis resources, then pins the backend
deployment to the exact CI commit image. The `:latest` tag in the manifest is a
safe fallback for manual bootstrapping only.
