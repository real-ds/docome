# Docome Security

## Threat Model

PDF and Office files are untrusted input.

## Required Protections

- MIME/content validation
- File size limits
- Page count limits
- Temporary isolated processing
- Path traversal prevention
- SSRF protection
- Safe subprocess execution
- No shell interpolation of user input
- Antivirus/malware scanning where appropriate
- Signed download URLs
- Authorization checks
- Rate limiting
- Audit logs

## Sensitive Documents

Processing architecture should support a mode where documents remain in
controlled storage and are automatically deleted after the configured
retention period.

## Secrets

Secrets must be provided through environment/secret management systems.
Never commit secrets to source control.

## Redaction

Redaction must remove underlying content, not merely draw a black shape
over it.
