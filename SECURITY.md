# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take the security of OpenCode Python seriously. If you have discovered a security vulnerability, we appreciate your help in disclosing it to us in a responsible manner.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them using GitHub's private vulnerability reporting feature:

1. Go to the [Security Advisories](https://github.com/opencode-ai/opencode_4py/security/advisories) page
2. Click "Report a vulnerability"
3. Fill out the form with details about the vulnerability

Alternatively, you can email us at: security@opencode-ai.example.com

### What to Include

Please include the following information in your report:

- Type of vulnerability (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the vulnerability
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability, including how an attacker might exploit it

### Response Timeline

- **Initial Response**: Within 48 hours, we will acknowledge receipt of your report
- **Status Update**: Within 7 days, we will provide an estimated timeline for a fix
- **Resolution**: We aim to release a fix within 30 days for critical vulnerabilities

### Disclosure Policy

- We follow the principle of **Coordinated Vulnerability Disclosure**
- We ask that you give us a reasonable amount of time to fix the issue before public disclosure
- We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Best Practices

When using OpenCode Python, please follow these security best practices:

### API Keys and Secrets

1. **Never commit API keys to version control**
   - Use environment variables: `export OPENAI_API_KEY="your-key"`
   - Use a secrets manager for production deployments
   - Add keys to `.gitignore` and `.env` files

2. **Use minimal permissions**
   - Only grant API keys the minimum permissions required
   - Rotate keys regularly
   - Use separate keys for development and production

### Input Validation

1. **Validate all user inputs**
   - Sanitize file paths to prevent directory traversal
   - Validate URLs before making requests
   - Be cautious with user-provided code execution

2. **Be careful with prompts**
   - User prompts may contain injection attacks
   - Validate and sanitize prompts before sending to LLMs

### Network Security

1. **Use HTTPS for all API calls**
   - OpenCode uses HTTPS by default
   - Do not disable certificate verification

2. **Local models**
   - When using Ollama or local models, ensure they're properly secured
   - Don't expose local model endpoints to untrusted networks

### Dependencies

1. **Keep dependencies updated**
   - Run `pip-audit` regularly to check for vulnerable dependencies
   - Use Dependabot for automated updates

2. **Review dependencies**
   - Only install trusted packages
   - Review the permissions requested by dependencies

## Security Features

OpenCode Python includes several security features:

- **Secret Filtering**: API keys and secrets are automatically filtered from logs
- **Input Sanitization**: File paths and commands are validated
- **Content Filtering**: RAG outputs can be filtered for sensitive content
- **Audit Logging**: Security-relevant events are logged

## Security Audit

We periodically conduct security audits and welcome community review:

- All code changes are reviewed before merging
- We use automated security scanning in CI
- We participate in responsible disclosure programs

## Contact

For general security questions (non-vulnerability reports):
- Open a GitHub Discussion: https://github.com/opencode-ai/opencode_4py/discussions
- Email: security@opencode-ai.example.com

---

*Last updated: 2026-02-23*