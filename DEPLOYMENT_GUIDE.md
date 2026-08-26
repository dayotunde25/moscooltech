# Production Deployment Guide - Moscool Technical Services

## Quick Start Checklist

### Step 1: Set Environment Variables on Render

Go to your Render service → **Settings → Environment**

Add these variables:

```bash
# === SECURITY (REQUIRED) ===
SECRET_KEY=<run-this-locally: python3 -c "import secrets; print(secrets.token_hex(32))">
ADMIN_PASSWORD=<your-strong-admin-password>

# === CONFIGURATION (REQUIRED) ===
FLASK_ENV=production
DATABASE_URL=<Render will provide if using PostgreSQL>
ADMIN_EMAIL=admin@moscooltech.com

# === OPTIONAL ===
NEWSDATA_API_KEY=<get-from-newsdata.io>
PORT=10000  # Render sets this automatically
```

### Step 2: Generate SECRET_KEY

Run this command on your local machine:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste into Render environment as `SECRET_KEY`.

### Step 3: Deploy

1. Push changes to GitHub
2. Render auto-deploys on push (if configured)
3. Wait for build to complete
4. Check **Logs** tab for any errors

### Step 4: First Login

1. Visit `https://your-app.onrender.com/admin/login`
2. Username: `admin`
3. Password: Value you set in `ADMIN_PASSWORD`
4. **IMMEDIATELY**: Change password in admin settings

---

## Environment Variables Explained

| Variable | Purpose | Example | Required? |
|----------|---------|---------|----------|
| `SECRET_KEY` | Encrypts session cookies | `a7f3e9d2b4c6...` | ✅ YES |
| `ADMIN_PASSWORD` | Initial admin login password | `MyStr0ng!Pass` | ✅ YES |
| `FLASK_ENV` | Production/development mode | `production` | ✅ YES |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` | ✅ YES (if using DB) |
| `ADMIN_EMAIL` | Admin account email | `admin@example.com` | ⚠️ Optional |
| `NEWSDATA_API_KEY` | News API integration | `abc123def456` | ⚠️ Optional |
| `PORT` | Server port | `10000` | Auto-set by Render |

---

## Security After Deployment

### Immediate Actions (Day 1)

1. **Change Admin Password**
   - Login to `/admin/login`
   - User profile → Change password
   - Use a strong, unique password

2. **Verify HTTPS**
   - Check URL bar for 🔒 lock icon
   - Visit https://securityheaders.com and enter your domain
   - Should show "A" or "A+" rating

3. **Test Security Headers**
   ```bash
   curl -I https://your-app.onrender.com
   ```
   Look for these headers:
   - `Strict-Transport-Security`
   - `X-Frame-Options: SAMEORIGIN`
   - `X-Content-Type-Options: nosniff`
   - `Content-Security-Policy`

4. **Check Robots.txt**
   - Visit `/robots.txt`
   - Should see crawling rules

5. **Verify Sitemap**
   - Visit `/sitemap.xml`
   - Should list home page and all published posts

### Ongoing (Weekly)

1. **Review Logs**
   - Check Render logs for errors
   - Look for repeated failed login attempts

2. **Monitor Site**
   - Verify all public pages load
   - Test contact/feedback forms

### Ongoing (Monthly)

1. **Update Dependencies**
   ```bash
   pip list --outdated
   # Update to latest safe versions
   pip install --upgrade Flask Flask-SQLAlchemy ...
   ```

2. **Review Admin Dashboard**
   - Check recent contacts
   - Verify post counts

3. **SEO Check**
   - Test Google Search Console
   - Monitor Core Web Vitals

---

## Troubleshooting

### "CSRF token missing" on forms

**Problem**: Forms reject valid submissions

**Solution**: 
- Clear browser cache/cookies
- Ensure JavaScript is enabled
- Check if form includes `{{ csrf_token() }}`

### Admin login always fails

**Problem**: Credentials don't work after deployment

**Solution**:
- Verify `ADMIN_PASSWORD` is set in Render environment
- Check Render logs: `View Logs` → search for "admin user created"
- Restart the service (Render dashboard → Manual Deploy)

### File uploads fail

**Problem**: "Invalid file type" when uploading images/videos

**Solution**:
- Use only PNG, JPG, GIF for images
- Use only MP4, AVI, MOV, WMV for videos
- File must be under 16MB
- Check file MIME type:
  ```bash
  file -b --mime-type myimage.jpg
  # Should output: image/jpeg
  ```

### Sitemap is empty

**Problem**: `/sitemap.xml` shows no posts

**Solution**:
- Create a post and set `published=true`
- Sitemap only includes published posts
- Reload sitemap after publishing

### Rate limiting too strict

**Problem**: Legitimate users locked out after "too many login attempts"

**Solution** (if needed, modify `app.py`):
```python
check_login_rate_limit(client_ip, max_attempts=10, window_seconds=1800)
# Increases to 10 attempts per 30 minutes
```

---

## Database Setup

### Option A: PostgreSQL (Recommended)

Render includes free PostgreSQL:

1. Go to Render dashboard
2. Create new PostgreSQL database
3. Copy connection string to `DATABASE_URL` env variable
4. Tables created automatically on app startup

### Option B: SQLite (Development Only)

Default fallback if no `DATABASE_URL`:

```bash
# Local development
DATABASE_URL=sqlite:///moscool_tech.db
python app.py
```

⚠️ **Not recommended for production**—data lost on redeploy

---

## Monitoring & Maintenance

### Check Application Status

```bash
# Render dashboard → Logs
# Look for these indicators:
✅ "Application running" - app is up
✅ "Background scheduler started" - news feed working
✅ "Admin user created" - on first deploy
⚠️ "Failed login attempt from IP" - monitor for brute force
❌ "Database connection error" - urgent fix needed
```

### Enable Error Tracking (Optional)

Consider integrating:
- **Sentry**: Real-time error monitoring
- **New Relic**: Performance monitoring
- **Datadog**: Infrastructure monitoring

---

## Backup & Recovery

### Database Backups

**PostgreSQL on Render**:
1. Render dashboard → Database
2. Backups tab → automatic daily backups
3. Download backup if needed

### Application Code

**GitHub**:
- All code in GitHub repository
- Render auto-deploys from main branch
- Easy rollback to previous commits if needed

### Manual Backup

```bash
# Backup database locally
pg_dump postgresql://user:pass@host/db > backup.sql

# Restore from backup
psql postgresql://user:pass@host/db < backup.sql
```

---

## Performance Optimization

### Current Setup

- ✅ Static files served with caching headers
- ✅ Bootstrap CDN for CSS/JS (fast, reliable)
- ✅ Render includes free SSL/TLS
- ✅ Database connection pooling

### Optional Improvements

1. **Add CDN (CloudFlare)**
   - Free tier available
   - Speeds up global access
   - DDoS protection included

2. **Image Optimization**
   - Use WebP format when possible
   - Compress images before upload
   - Lazy load images below fold

3. **Caching**
   - Add Redis for session caching
   - Cache API responses

---

## Custom Domain Setup

1. **Purchase Domain**
   - GoDaddy, Namecheap, Google Domains, etc.

2. **Point to Render**
   - Render dashboard → Settings → Custom Domains
   - Add your domain (e.g., `moscooltech.com`)
   - Follow DNS instructions (CNAME record)

3. **Wait for DNS Propagation**
   - Usually 5-30 minutes
   - Check with: `nslookup moscooltech.com`

4. **Verify SSL Certificate**
   - Render auto-generates certificate
   - Green lock should appear
   - Takes up to 1 minute after DNS updates

---

## Email Configuration (For Notifications)

Currently, contact/feedback forms store data in database. To add email notifications:

1. **Add Email Library**
   ```bash
   pip install Flask-Mail
   ```

2. **Update .env**
   ```bash
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   ```

3. **Modify app.py** (see Flask-Mail documentation)

---

## Support

### Resources

- **Flask Documentation**: https://flask.palletsprojects.com/
- **Render Docs**: https://render.com/docs
- **SQLAlchemy ORM**: https://docs.sqlalchemy.org/
- **Bootstrap**: https://getbootstrap.com/docs/5.3/

### Getting Help

1. Check logs: `Render Dashboard → Logs`
2. Review error templates
3. Test locally: `python app.py`
4. Check GitHub issues for similar problems
5. Contact development team

---

## Version History

| Version | Date | Changes |
|---------|------|----------|
| 1.0 | 2026-08-26 | Initial security & SEO audit |

---

**Last Updated**: August 26, 2026
**Status**: Production Ready ✅
