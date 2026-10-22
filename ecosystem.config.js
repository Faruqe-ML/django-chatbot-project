// PM2 process file for the Django chatbot.
// On the server: pm2 start ecosystem.config.js
//
// Edit env below before the first start:
//   DJANGO_ALLOWED_HOSTS  server IP and domain, comma-separated
//   DJANGO_SECRET_KEY     long random string
// Put OPENAI_API_KEY in a .env file in this same folder.

const path = require("path");

module.exports = {
  apps: [
    {
      name: "django-chatbot",
      cwd: __dirname,
      script: path.join(__dirname, "venv", "bin", "gunicorn"),
      args: [
        "ChatBot.wsgi:application",
        "--bind", "0.0.0.0:8000",
        "--workers", "1",
        "--timeout", "180",
        "--graceful-timeout", "30",
        "--access-logfile", "-",
        "--error-logfile", "-",
      ].join(" "),
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      env: {
        DJANGO_DEBUG: "False",
        DJANGO_ALLOWED_HOSTS: "127.0.0.1,localhost,192.168.1.235,103.80.161.158",
        DJANGO_SECRET_KEY: "change-this-before-going-live",
        // DJANGO_CSRF_TRUSTED_ORIGINS: "https://your-domain.com",
        // DJANGO_BEHIND_HTTPS_PROXY: "True",
      },
    },
  ],
};
