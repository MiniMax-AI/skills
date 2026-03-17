# Privacy & Security Guidelines

Security best practices and privacy requirements for Android applications.

## Permissions

### Principle of Least Privilege

| Rule | Implementation |
|------|----------------|
| Request minimum | Only permissions essential for core features |
| Request when needed | At point of use, not app startup |
| Explain why | Show rationale before system dialog |
| Degrade gracefully | App works (limited) if denied |

### Permission Request Flow

1. Check if already granted
2. If not, show educational UI (rationale)
3. Request permission
4. Handle result (grant or denial)
5. If denied, offer alternative or reduced functionality

### Sensitive Permissions

| Permission | Consideration |
|------------|---------------|
| Location | Use coarse if fine not needed |
| Camera | Request only when capturing |
| Microphone | Request only when recording |
| Contacts | Consider contact picker intent |
| Storage | Use scoped storage |
| SMS/Call Log | Restricted, needs approval |

### Alternative Approaches

| Instead of... | Consider... |
|---------------|-------------|
| READ_CONTACTS | Contact picker intent |
| ACCESS_FINE_LOCATION | Coarse location |
| READ_EXTERNAL_STORAGE | Storage Access Framework |
| CAMERA | Camera intent |

## Data Storage

### Storage Types

| Type | Security | Usage |
|------|----------|-------|
| Internal storage | Private to app | Sensitive data |
| External storage | World-readable | Shared files only |
| SharedPreferences | Private, unencrypted | Non-sensitive settings |
| EncryptedSharedPreferences | Private, encrypted | Sensitive settings |
| Room database | Private, optional encryption | Structured data |

### Sensitive Data Rules

| Rule | Implementation |
|------|----------------|
| Store internally | Use internal storage, not external |
| Encrypt at rest | Use EncryptedSharedPreferences, SQLCipher |
| Don't log | Never log PII or credentials |
| Clear on logout | Wipe user data completely |

### Data Logging

Never log sensitive data such as passwords, emails, tokens, or personal information. Only log non-sensitive operational information.

## Network Security

### HTTPS Requirements

- All network traffic must use SSL/TLS
- Configure Network Security Config
- Don't allow cleartext traffic

### Network Security Config

Define a network security configuration that:
- Disables cleartext traffic
- Specifies trusted certificate authorities
- Optionally implements certificate pinning for high-security apps

### Certificate Pinning (Optional)

For high-security apps, pin certificates to prevent MITM attacks. Include backup pins and plan for certificate rotation.

## User Identity

### Credential Manager

Integrate Credential Manager for unified sign-in supporting:
- Passkeys
- Federated identity
- Traditional passwords

### Biometric Authentication

Use biometric authentication for sensitive operations like:
- Financial transactions
- Accessing sensitive documents
- Confirming identity

### Autofill Support

Provide autofill hints on input fields:
- emailAddress, username for identity fields
- password for credential fields
- creditCardNumber, postalCode for payment fields

## App Components Security

### Exported Components

| Component | Exported Rule |
|-----------|---------------|
| Launcher Activity | exported="true" with intent-filter |
| Internal Activity | exported="false" |
| Internal Service | exported="false" |
| Content Provider (shared) | exported="true" with permissions |

Always explicitly set the exported attribute on all components.

### Custom Permissions

Use signature-level protection for custom permissions that control access between your own apps.

### Intent Validation

- Validate all intent data before use
- Check URI scheme and host
- Use explicit intents when possible
- Don't trust extras from unknown sources

### PendingIntent Security

Use FLAG_IMMUTABLE for PendingIntents unless mutability is required. This prevents other apps from modifying the intent.

## WebView Security

### Safe WebView Configuration

| Setting | Recommendation |
|---------|----------------|
| JavaScript | Disabled unless required |
| File access | Disabled |
| Content access | Disabled |
| Universal file access | Never enable |

### Avoid Dangerous Practices

| Don't | Why |
|-------|-----|
| setAllowUniversalAccessFromFileURLs(true) | Security vulnerability |
| addJavascriptInterface() with untrusted content | Code injection risk |
| Load untrusted URLs | XSS, phishing |

## Cryptography

### Use Platform APIs

- Use Android Keystore for key storage
- Use standard algorithms (AES-GCM, RSA)
- Never implement custom cryptography
- Use SecureRandom for random generation

### Avoid

- Custom encryption implementations
- Weak algorithms (MD5, SHA1 for security)
- Hardcoded keys or secrets
- Non-cryptographic random generators

## Code Security

### No Dynamic Code Loading

| Don't | Do Instead |
|-------|------------|
| Load code at runtime | Android App Bundles |
| Download DEX files | Play Feature Delivery |
| Execute scripts | Predefined functionality |

### Debug Code Removal

- Set debuggable=false in release builds
- Enable minification (R8/ProGuard)
- Remove debug libraries from production

## Device Identifiers

### Don't Use Hardware IDs

| Identifier | Status |
|------------|--------|
| IMEI | Don't use |
| MAC address | Don't use |
| Serial number | Don't use |
| Android ID | Limited use only |

### Recommended Alternatives

| Use Case | Solution |
|----------|----------|
| Analytics | Firebase Analytics ID |
| Advertising | Advertising ID (resettable) |
| App instance | Generate UUID on install |
| User identity | Account-based ID |

## Google Play Policies

### Data Safety

- Declare all data collected
- Explain data usage
- Provide privacy policy
- Allow data deletion requests

### User Data Policy

| Rule | Requirement |
|------|-------------|
| Transparency | Clear disclosure of data use |
| Security | Protect user data appropriately |
| Minimization | Collect only what's needed |
| Control | Allow users to manage data |

## Security Checklist

- [ ] Permissions requested only when needed
- [ ] Permissions explained to user
- [ ] Sensitive data stored internally
- [ ] No sensitive data in logs
- [ ] All network traffic over HTTPS
- [ ] Network security config defined
- [ ] Components export status explicit
- [ ] Custom permissions use signature protection
- [ ] Intents validated before use
- [ ] PendingIntents use FLAG_IMMUTABLE
- [ ] WebView configured securely
- [ ] Platform crypto APIs used
- [ ] No debug code in production
- [ ] No hardware IDs used
- [ ] Privacy policy available
