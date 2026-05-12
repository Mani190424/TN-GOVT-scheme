# 🚀 Deployment Guide - TN GOVT SCHEME BOT

Complete deployment instructions for various hosting platforms.

---

## 📋 Pre-Deployment Checklist

- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with all required variables
- [ ] Database schema initialized (`mysql < database.sql`)
- [ ] Application tested locally (`python app.py`)
- [ ] OpenAI API key obtained and verified
- [ ] MySQL server configured and accessible
- [ ] Static files and templates verified

---

## 🖥️ Local Deployment (Development)

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/tn-scheme-bot.git
cd tn-scheme-bot
```

### 2. Setup Python Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Database
```bash
# MySQL
mysql -u root -p < database.sql
```

### 5. Create Environment File
```bash
cp .env.example .env
# Edit .env with your values
```

### 6. Run Application
```bash
python app.py
```

Access at: `http://localhost:5000`

---

## ☁️ Heroku Deployment

### Prerequisites
- Heroku account
- Heroku CLI installed
- Git repository

### 1. Create Heroku App
```bash
heroku login
heroku create tn-scheme-bot
```

### 2. Add MySQL Database
```bash
# Using ClearDB
heroku addons:create cleardb:ignite
```

### 3. Set Environment Variables
```bash
heroku config:set FLASK_ENV=production
heroku config:set OPENAI_API_KEY=sk-your-key
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DB_HOST=your-db-host
heroku config:set DB_USER=your-db-user
heroku config:set DB_PASSWORD=your-db-password
heroku config:set DB_NAME=your-db-name
```

### 4. Create Procfile
```
web: gunicorn app:app
```

### 5. Deploy
```bash
git push heroku main
```

### 6. Initialize Database
```bash
heroku run mysql < database.sql
```

### 7. View Logs
```bash
heroku logs --tail
```

---

## 🌐 AWS Deployment (Elastic Beanstalk)

### 1. Install EB CLI
```bash
pip install awsebcli
```

### 2. Initialize EB Application
```bash
eb init -p python-3.9 tn-scheme-bot --region us-east-1
```

### 3. Create Environment
```bash
eb create tn-scheme-bot-env
```

### 4. Configure Environment Variables
Create `.ebextensions/app_env.config`:
```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    FLASK_ENV: production
    OPENAI_API_KEY: sk-your-key
    SECRET_KEY: your-secret-key
```

### 5. Configure RDS Database
```bash
eb create --instance-type t2.micro --db.engine mysql --db.version 8.0
```

### 6. Deploy
```bash
eb deploy
```

### 7. Monitor
```bash
eb status
eb logs
```

---

## 🐳 Docker Deployment

### 1. Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
```

### 2. Create Docker Compose File
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DB_HOST=db
      - DB_USER=root
      - DB_PASSWORD=password
      - DB_NAME=tn_scheme_bot
    depends_on:
      - db
    volumes:
      - ./flask_session:/app/flask_session

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=tn_scheme_bot
    volumes:
      - mysql_data:/var/lib/mysql
      - ./database.sql:/docker-entrypoint-initdb.d/database.sql

volumes:
  mysql_data:
```

### 3. Build and Run
```bash
docker-compose build
docker-compose up
```

### 4. Access Application
Visit `http://localhost:5000`

---

## 📦 DigitalOcean Deployment

### 1. Create Droplet
- Select Ubuntu 20.04 LTS
- Choose $5/month plan (minimum)
- Generate SSH key

### 2. Connect via SSH
```bash
ssh root@your_droplet_ip
```

### 3. Update System
```bash
apt update
apt upgrade -y
```

### 4. Install Dependencies
```bash
apt install -y python3-pip python3-venv mysql-server nginx
```

### 5. Clone Repository
```bash
git clone https://github.com/yourusername/tn-scheme-bot.git
cd tn-scheme-bot
```

### 6. Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 7. Configure MySQL
```bash
mysql -u root -p < database.sql
```

### 8. Create .env File
```bash
cp .env.example .env
nano .env  # Edit with your values
```

### 9. Configure Nginx
Create `/etc/nginx/sites-available/tn-scheme-bot`:
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /home/ubuntu/tn-scheme-bot/static/;
    }
}
```

### 10. Enable Nginx Config
```bash
ln -s /etc/nginx/sites-available/tn-scheme-bot /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### 11. Setup Systemd Service
Create `/etc/systemd/system/tn-scheme-bot.service`:
```ini
[Unit]
Description=TN Scheme Bot Flask Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/tn-scheme-bot
Environment="PATH=/home/ubuntu/tn-scheme-bot/venv/bin"
ExecStart=/home/ubuntu/tn-scheme-bot/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

### 12. Start Service
```bash
systemctl daemon-reload
systemctl start tn-scheme-bot
systemctl enable tn-scheme-bot
```

### 13. Setup SSL with Let's Encrypt
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your_domain.com
```

---

## 🔒 Production Security Checklist

### Flask Configuration
```python
FLASK_ENV = 'production'
DEBUG = False
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
PERMANENT_SESSION_LIFETIME = 3600
```

### Database Security
```sql
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE ON tn_scheme_bot.* TO 'app_user'@'localhost';
```

### Nginx Configuration
```nginx
# Add security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
```

### Firewall Rules
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

---

## 📊 Performance Optimization

### Enable Gzip Compression
```nginx
gzip on;
gzip_types text/plain text/css text/xml text/javascript
            application/x-javascript application/xml+rss;
```

### Configure Caching Headers
```nginx
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### Database Connection Pooling
```python
# In app.py
from flask_mysqldb import MySQL
mysql = MySQL()
mysql.init_app(app)
```

---

## 🔍 Monitoring & Logging

### Application Logs
```bash
# View logs
tail -f /var/log/tn-scheme-bot.log

# Rotate logs
logrotate /etc/logrotate.d/tn-scheme-bot
```

### System Monitoring
```bash
# CPU and Memory
htop

# Disk Space
df -h

# MySQL Status
mysqladmin -u root -p status
```

### Health Check
```python
@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200
```

---

## 🚨 Backup & Recovery

### Database Backup
```bash
# Automatic daily backup
0 2 * * * mysqldump -u root -p tn_scheme_bot > /backups/tn_scheme_bot_$(date +\%Y\%m\%d).sql

# Manual backup
mysqldump -u root -p tn_scheme_bot > backup.sql
```

### Restore Database
```bash
mysql -u root -p tn_scheme_bot < backup.sql
```

### File Backup
```bash
tar -czf tn-scheme-bot-backup.tar.gz /home/ubuntu/tn-scheme-bot
```

---

## 🔄 Update & Maintenance

### Update Application
```bash
cd /home/ubuntu/tn-scheme-bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart tn-scheme-bot
```

### Database Migration
```bash
# Backup first
mysqldump -u root -p tn_scheme_bot > backup.sql

# Apply schema changes
mysql -u root -p < database_migration.sql
```

---

## 📈 Scaling Strategy

### Horizontal Scaling
```yaml
# Using Docker Swarm
docker service create \
  --replicas 3 \
  --name tn-scheme-bot \
  tn-scheme-bot:latest
```

### Load Balancing
```nginx
upstream app_backend {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

server {
    location / {
        proxy_pass http://app_backend;
    }
}
```

---

## 🆘 Troubleshooting

### Application Won't Start
```bash
# Check logs
journalctl -u tn-scheme-bot -n 50

# Test configuration
python app.py

# Check port
netstat -tlnp | grep 5000
```

### Database Connection Error
```bash
# Test MySQL
mysql -u root -p -e "SELECT 1;"

# Check permissions
GRANT ALL PRIVILEGES ON tn_scheme_bot.* TO 'app_user'@'localhost';
```

### High Memory Usage
```bash
# Restart service
systemctl restart tn-scheme-bot

# Check for leaks
ps aux | grep gunicorn
```

---

## 📞 Support

For deployment issues, check logs and contact support:
- **Email**: deploy-support@tnschemebot.gov.in
- **Slack**: #deployments channel
- **Documentation**: https://docs.tnschemebot.gov.in

---

**Last Updated**: May 2026  
**Version**: 1.0.0
