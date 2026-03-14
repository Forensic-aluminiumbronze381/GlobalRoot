# Security Policy

## Supported Version

Security fixes are provided on the latest version in the default branch.

## Reporting a Vulnerability

Please do not open public issues for security vulnerabilities.

Instead, provide a private report with:

- A clear description of the issue
- Steps to reproduce
- Potential impact
- Suggested mitigation (if available)

If private reporting channels are not yet configured, open an issue titled `Security report requested` without sensitive details, and ask for a private contact route.

## Security Notes for Users

This project can execute commands and write files in allowed directories.

To reduce risk:

- Use dedicated sandbox directories in `ALLOWED_DIRS`
- Avoid granting access to important personal/system/backup folders
- Review tool outputs before extending permissions
- Keep local models and dependencies updated
