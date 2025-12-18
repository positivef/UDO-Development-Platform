# Secrets Directory

This directory contains sensitive credentials used by Docker secrets in `docker-compose.secure.yml`.

## Setup

### 1. Generate Database Password

```bash
openssl rand -base64 32 > db_password.txt
```

### 2. Add API Keys

Create the following files with your actual API keys:

- `openai_api_key.txt` - OpenAI API key (format: `sk-...`)
- `anthropic_api_key.txt` - Anthropic Claude API key (format: `sk-ant-...`)
- `gemini_api_key.txt` - Google Gemini API key

Example:
```bash
echo "sk-YOUR_OPENAI_KEY_HERE" > openai_api_key.txt
echo "sk-ant-YOUR_ANTHROPIC_KEY_HERE" > anthropic_api_key.txt
echo "YOUR_GEMINI_KEY_HERE" > gemini_api_key.txt
```

### 3. Set Permissions

```bash
# Make secrets read-only for owner
chmod 600 *.txt

# Verify permissions
ls -la
```

## Security Notes

- **NEVER** commit these files to version control
- Each file should contain only the secret value (no extra whitespace)
- Use strong, randomly generated passwords
- Rotate secrets regularly (every 90 days recommended)
- Backup secrets securely (encrypted storage)

## File List

Expected files:
- `db_password.txt` - PostgreSQL password
- `openai_api_key.txt` - OpenAI API key
- `anthropic_api_key.txt` - Anthropic API key
- `gemini_api_key.txt` - Google Gemini API key

## Troubleshooting

### File Not Found Error

If Docker fails to find secrets:
```bash
# Check files exist
ls -la secrets/

# Check permissions
stat secrets/db_password.txt

# Verify no trailing newlines
cat -A secrets/db_password.txt
```

### Permission Denied

If permission errors occur:
```bash
# Fix ownership
sudo chown $USER:$USER secrets/*.txt

# Fix permissions
chmod 600 secrets/*.txt
```
