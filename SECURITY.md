# Security Policy

## Supported Versions

We release patches for security vulnerabilities regularly. Here are the currently supported versions:

| Version | Supported          | End of Support |
| ------- | ------------------ | -------------- |
| 1.x.x   | :white_check_mark: | Current        |
| 0.2.x   | :white_check_mark: | 2025-12-31     |
| 0.1.x   | :x:                | Ended          |

## Reporting a Vulnerability

We take the security of Sales Agentic Army seriously. If you believe you've found a security vulnerability, please report it to us as described below.

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to **security@sales-agentic-army.io** with the following information:

1. Description of the vulnerability
2. Steps to reproduce the issue
3. Potential impact assessment
4. Any suggested fixes (if applicable)

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

After the initial reply to your report, the security team will keep you informed of the progress towards a fix and full announcement, and may ask for additional information or guidance.

## Security Best Practices

When deploying Sales Agentic Army in production, please ensure:

- ✅ All secrets are stored in HashiCorp Vault or equivalent
- ✅ mTLS is enabled between all services
- ✅ Network policies restrict pod-to-pod communication
- ✅ Regular security updates are applied
- ✅ Audit logging is enabled and monitored
- ✅ RBAC is properly configured

## Bug Bounty Program

We offer a bug bounty program for critical security vulnerabilities. Please contact security@sales-agentic-army.io for details.

## PGP Key

For encrypted communication, please use our PGP key:

```
-----BEGIN PGP PUBLIC KEY BLOCK-----
[PGP key would be here]
-----END PGP PUBLIC KEY BLOCK-----
```

Key fingerprint: `XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX`
