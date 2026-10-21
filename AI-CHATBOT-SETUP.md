# StaxTech AI Chatbot Setup

The homepage widget sends questions to `/api/chat.php`. The PHP endpoint acts as a server-side proxy for an OpenAI-compatible chat-completions API so the secret API key is never delivered to visitors' browsers.

## 1. Upload/deploy
Deploy `api/chat.php` on the same PHP-enabled host as the website. PHP cURL must be enabled. If the site is hosted on static-only GitHub Pages, this endpoint will not run there: deploy it to PHP hosting or replace it with a serverless function.

## 2. Configure secrets on the server (not in Git)
Set these environment variables in your hosting control panel or server configuration:

- `AI_API_URL`: HTTPS chat-completions endpoint from your AI provider
- `AI_API_KEY`: secret API key for that provider
- `AI_MODEL`: model identifier supported by the provider

This proxy currently expects an OpenAI-compatible JSON API with a `choices[0].message.content` response. The supplied key prefix alone is not enough to determine the correct provider endpoint/model. Confirm your provider's API docs before configuring these values.

## 3. Key safety
Never paste API keys into `index.html`, JavaScript, public repositories, chat transcripts, or client-side environment variables. Since a key was shared in chat, revoke/rotate it with its provider before using the replacement on the server.

## 4. Smoke test
With the environment configured, open the homepage, click the chat bubble, ask a test question, and check the browser Network tab for `POST /api/chat.php`. If it returns 503, the host environment variables are not configured. If the site is static-only or does not support PHP, the API endpoint needs to be deployed separately.
