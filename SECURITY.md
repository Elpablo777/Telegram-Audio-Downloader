# Security Policy

## Supported Versions

We release security patches for the latest version of the Telegram Audio Downloader.

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it by emailing hannover84@msn.com.

Please include the following information in your report:
- Description of the vulnerability
- Steps to reproduce the vulnerability
- Potential impact of the vulnerability
- Any possible mitigations you've identified

We will acknowledge your report within 48 hours and will strive to provide a fix within 7 days.

## Security Updates

This project uses Dependabot to automatically update dependencies. Security-critical packages including:
- cryptography
- aiohttp
- tqdm

Are monitored more closely and updated with higher priority.

## Vulnerability Disclosure Policy

We follow a coordinated disclosure policy:
1. Vulnerabilities are confirmed and validated
2. Patches are developed and tested
3. A new release is published with the fix
4. The vulnerability is publicly disclosed after the fix is available

## Security Best Practices

This project follows these security practices:
- Regular dependency updates
- Automated security scanning
- Code review for security implications
- Secure handling of credentials and secrets