# Auth System Refactoring Plan

## Overview

This document outlines a comprehensive refactoring plan for the authentication system across 4 focus areas: Code Quality & Architecture, Security Enhancements, Feature Completeness, and Performance & Scalability. The plan is organized into phases with checkpoints after each phase.

**Estimated Timeline:** 12-16 days
**Approach:** Phase-based execution with checkpoints after each phase
**Risk Level:** Medium (mitigated through incremental implementation and testing)

---

## Table of Contents

1. [Phase 1: Code Quality & Architecture](#phase-1-code-quality--architecture)
2. [Phase 2: Security Enhancements](#phase-2-security-enhancements)
3. [Phase 3: Feature Completeness](#phase-3-feature-completeness)
4. [Phase 4: Performance & Scalability](#phase-4-performance--scalability)
5. [Implementation Order & Dependencies](#implementation-order--dependencies)
6. [Risk Mitigation](#risk-mitigation)
7. [Success Metrics](#success-metrics)

---

## Phase 1: Code Quality & Architecture (Foundation)

**Duration:** 2-3 days | **Risk:** Low | **Impact:** High

### Overview

This phase focuses on establishing a solid foundation by improving code quality, reducing duplication, and establishing consistent patterns across the codebase.

### 1.1 Base Repository Pattern

**Goal:** Reduce code duplication in repository layer

#### Tasks

- [ ] Create `BaseRepository` class with common CRUD operations
- [ ] Implement generic `get_by_id`, `list`, `exists` methods
- [ ] Extract transaction management pattern
- [ ] Add query builder pattern for complex queries

#### Files to Create/Modify

**New Files:**

```
app/repositories/base.py
```

**Modified Files:**

```
app/repositories/users_repositories.py
app/repositories/sessions_repo.py
```

#### Implementation Details

```python
# app/repositories/base.py (simplified example)
from typing import TypeVar, Type, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')

class BaseRepository:
    def __init__(self, db: AsyncSession, model: Type[T]):
        self.db = db
        self.model = model

    async def get_by_id(self, id: int) -> Optional[T]:
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, limit: int = 100, offset: int = 0) -> List[T]:
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def exists(self, **kwargs) -> bool:
        stmt = select(self.model).filter_by(**kwargs)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def add(self, entity: T) -> T:
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def save(self) -> None:
        await self.db.commit()
```

#### Benefits

- ~30% code reduction in repositories
- Consistent error handling
- Easier to add new entities
- Type-safe operations

---

### 1.2 Service Layer Improvements

**Goal:** Extract common patterns and improve testability

#### Tasks

- [ ] Create `BaseService` abstract class
- [ ] Extract `_now()` method to time provider (for testing)
- [ ] Add result pattern (Success/Failure) instead of exceptions
- [ ] Implement validation decorator pattern

#### Files to Create/Modify

**New Files:**

```
app/services/base.py
app/core/utils/time_provider.py
app/core/results/result.py
app/core/decorators/validation.py
```

**Modified Files:**

```
app/services/auth/auth_services.py
app/services/sessions/session_services.py
```

#### Implementation Details

```python
# app/core/utils/time_provider.py
from datetime import UTC, datetime
from abc import ABC, abstractmethod

class TimeProvider(ABC):
    @abstractmethod
    def now(self) -> datetime:
        pass

class DefaultTimeProvider(TimeProvider):
    def now(self) -> datetime:
        return datetime.now(UTC)

class TestTimeProvider(TimeProvider):
    def __init__(self, fixed_time: datetime):
        self._fixed_time = fixed_time

    def now(self) -> datetime:
        return self._fixed_time

# app/core/results/result.py
from dataclasses import dataclass
from typing import TypeVar, Generic

T = TypeVar('T')

@dataclass
class Success(Generic[T]):
    value: T
    message: str = "Operation successful"

@dataclass
class Failure:
    error: str
    message: str
    details: dict | None = None

Result = Success[T] | Failure
```

#### Benefits

- Better testability (mockable time)
- Consistent service behavior
- Clear success/failure handling
- Reduced exception handling overhead

---

### 1.3 Dependency Injection Improvements

**Goal:** Reduce dependency chain complexity

#### Tasks

- [ ] Create dependency container with FastAPI's `Depends` optimization
- [ ] Add caching for singleton services
- [ ] Implement lazy-loading for expensive services
- [ ] Create factory pattern for service instantiation

#### Files to Create/Modify

**New Files:**

```
app/api/containers.py
app/api/factories.py
```

**Modified Files:**

```
app/api/deps.py
app/main.py
```

#### Implementation Details

```python
# app/api/containers.py
from functools import lru_cache
from fastapi import Depends
from app.services.auth.auth_services import AuthService
from app.services.jwt.jwt_service import JwtService
from app.services.sessions.session_services import SessionService

class ServiceContainer:
    @staticmethod
    @lru_cache(maxsize=1)
    def jwt_service() -> JwtService:
        from app.core.settings import get_app_settings
        from app.services.jwt.jwt_service import JwtService
        return JwtService(get_app_settings().jwt)

    @staticmethod
    def auth_service(
        jwt: JwtService = Depends(lambda: ServiceContainer.jwt_service()),
        session_service: SessionService = Depends(get_session_service),
        user_repo: UserRepository = Depends(get_user_repo),
    ) -> AuthService:
        from app.core.settings import get_app_settings
        return AuthService(jwt, session_service, user_repo, get_app_settings().jwt)
```

#### Benefits

- Faster dependency resolution
- Better memory usage (LRU caching)
- Easier to test (injectable dependencies)
- Clear dependency graph

---

### 1.4 Configuration & Settings

**Goal:** Better organization and type safety

#### Tasks

- [ ] Split settings by domain (AuthConfig, SecurityConfig, etc.)
- [ ] Add settings validation
- [ ] Implement feature flags
- [ ] Add environment-specific overrides

#### Files to Create/Modify

**New Files:**

```
app/core/config/auth.py
app/core/config/security.py
app/core/config/feature_flags.py
app/core/config/database.py
app/core/config/cache.py
```

**Modified Files:**

```
app/core/settings.py
```

#### Implementation Details

```python
# app/core/config/security.py
from pydantic_settings import BaseSettings

class SecurityConfig(BaseSettings):
    model_config = {"env_prefix": "SECURITY_"}

    # Rate limiting
    login_attempts_per_minute: int = 5
    refresh_attempts_per_minute: int = 10

    # Password policies
    min_password_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special_chars: bool = True
    prevent_password_reuse: int = 5
    password_expiration_days: int = 90

    # Session policies
    max_concurrent_sessions: int = 3
    inactivity_timeout_minutes: int = 30
    bind_to_ip: bool = False

# app/core/config/feature_flags.py
class FeatureFlags(BaseSettings):
    model_config = {"env_prefix": "FEATURE_"}

    enable_2fa: bool = False
    enable_oauth: bool = False
    enable_password_reset: bool = True
    enable_email_verification: bool = True
    enable_account_lockout: bool = True
```

#### Benefits

- Clearer configuration structure
- Type-safe configuration access
- Easier to test with different configs
- Better error messages on invalid config

---

### 1.5 Documentation & Docstrings

**Goal:** Complete all TODO docstrings

#### Tasks

- [ ] Complete all module docstrings
- [ ] Add type hints to all public methods
- [ ] Create architecture documentation
- [ ] Add usage examples in docstrings

#### Files to Create/Modify

**New Files:**

```
docs/architecture.md
docs/auth_flow.md
docs/api_reference.md
docs/contributing.md
```

**Modified Files:**

- All files with TODO comments (approx. 15-20 files)

#### Documentation Structure

```markdown
# docs/architecture.md
## Table of Contents
- Overview
- Project Structure
- Architecture Patterns
  - Repository Pattern
  - Service Layer
  - Dependency Injection
- Data Flow
- Security Architecture
```

#### Benefits

- Better onboarding for new developers
- Self-documenting code
- Easier maintenance
- Reduced knowledge silos

---

### Phase 1 Checkpoint

#### Deliverables

- [x] Base repository pattern implemented
- [x] Base service pattern implemented
- [x] Dependency injection optimized
- [x] Configuration split and validated
- [x] Documentation complete
- [x] All tests passing

#### Acceptance Criteria

- Code coverage > 85%
- All existing tests pass
- No breaking changes to API
- Architecture documented
- No TODO comments remaining

#### Testing Checklist

- [ ] Unit tests for BaseRepository
- [ ] Unit tests for BaseService
- [ ] Integration tests for DI container
- [ ] Configuration validation tests
- [ ] Performance benchmarks (before/after)

---

## Phase 2: Security Enhancements

**Duration:** 3-4 days | **Risk:** Medium | **Impact:** Critical

### Overview

This phase focuses on hardening the authentication system against common security threats and vulnerabilities identified in OWASP Top 10.

### 2.1 Rate Limiting

**Goal:** Prevent brute force and DDoS attacks

#### Tasks

- [ ] Implement IP-based rate limiting
- [ ] Implement user-based rate limiting
- [ ] Add rate limiting for auth endpoints
- [ ] Add rate limiting for sensitive operations
- [ ] Configure rate limits in settings
- [ ] Add rate limit headers in responses

#### Files to Create/Modify

**New Files:**

```
app/core/security/rate_limiter.py
app/core/security/middleware.py
```

**Modified Files:**

```
app/core/config/security.py
app/api/v1/auth.py
pyproject.toml (add slowapi or fastapi-limiter)
```

#### Implementation Details

```python
# app/core/security/rate_limiter.py
from fastapi import Request, HTTPException, status
from functools import wraps
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

def rate_limit(times: int, seconds: int):
    def decorator(func):
        @wraps(func)
        @limiter.limit(f"{times}/{seconds} seconds")
        async def wrapper(request: Request, *args, **kwargs):
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage in auth.py
@router.post("/login")
@rate_limit(times=5, seconds=60)
async def login(...):
    ...
```

#### Configuration

```python
# SecurityConfig
login_attempts_per_minute: int = 5
refresh_attempts_per_minute: int = 10
password_reset_attempts_per_hour: int = 3
api_requests_per_minute: int = 60
```

#### Benefits

- Prevents brute force attacks
- Protects against DDoS
- Improves system stability
- Fair resource allocation

---

### 2.2 Account Lockout

**Goal:** Prevent credential stuffing attacks

#### Tasks

- [ ] Track failed login attempts per user
- [ ] Implement progressive lockout (5min, 15min, 1hr)
- [ ] Add account unlock mechanisms
- [ ] Create lockout events in audit log
- [ ] Add admin endpoint to unlock accounts
- [ ] Send email notifications on lockout

#### Files to Create/Modify

**New Files:**

```
app/services/auth/account_lockout.py
app/api/v1/admin/users.py
```

**Modified Files:**

```
app/models/users.py (add fields)
app/repositories/users_repositories.py (add methods)
app/services/auth/auth_services.py (add lockout logic)
app/api/v1/auth.py (update login)
```

#### Database Migration

```sql
ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TIMESTAMP NULL;
ALTER TABLE users ADD COLUMN previous_login_attempts JSONB DEFAULT '[]'::jsonb;
```

#### Implementation Details

```python
# Progressive lockout logic
ATTEMPT_THRESHOLDS = [
    (3, 5 * 60),      # 3 attempts -> 5 minutes
    (5, 15 * 60),     # 5 attempts -> 15 minutes
    (7, 60 * 60),     # 7 attempts -> 1 hour
    (10, 24 * 60 * 60) # 10 attempts -> 24 hours
]

async def handle_failed_login(user: User):
    user.failed_login_attempts += 1

    for threshold, duration in ATTEMPT_THRESHOLDS:
        if user.failed_login_attempts >= threshold:
            user.locked_until = datetime.now(UTC) + timedelta(seconds=duration)
            await notify_user_locked(user, duration)
            break

    await user_repo.save()
```

#### Benefits

- Prevents credential stuffing
- Protects user accounts
- Deters attackers
- Improves security posture

---

### 2.3 Password Policies

**Goal:** Enforce strong password requirements

#### Tasks

- [ ] Implement password complexity validator
- [ ] Add password history check (prevent reuse)
- [ ] Implement password expiration policy
- [ ] Add password strength meter
- [ ] Create password change flow
- [ ] Add password requirements in UI

#### Files to Create/Modify

**New Files:**

```
app/core/security/password_validator.py
app/api/v1/users/password.py
app/schemas/user.py (password-related schemas)
```

**Modified Files:**

```
app/models/users.py (add fields)
app/core/config/security.py (add password policies)
app/services/auth/auth_services.py
```

#### Database Migration

```sql
ALTER TABLE users ADD COLUMN password_history JSONB DEFAULT '[]'::jsonb;
ALTER TABLE users ADD COLUMN password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN password_expires_at TIMESTAMP NULL;
```

#### Implementation Details

```python
# app/core/security/password_validator.py
import re
from dataclasses import dataclass
from typing import List

@dataclass
class PasswordPolicy:
    min_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special_chars: bool = True
    prevent_reuse: int = 5
    expiration_days: int = 90

@dataclass
class PasswordValidationResult:
    is_valid: bool
    errors: List[str]
    strength_score: int  # 0-100

class PasswordValidator:
    def __init__(self, policy: PasswordPolicy):
        self.policy = policy

    def validate(self, password: str, user_history: List[str] = None) -> PasswordValidationResult:
        errors = []
        strength_score = 0

        # Length check
        if len(password) < self.policy.min_length:
            errors.append(f"Password must be at least {self.policy.min_length} characters")
        else:
            strength_score += 20

        # Uppercase check
        if self.policy.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain uppercase letters")
        else:
            strength_score += 20

        # Lowercase check
        if self.policy.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain lowercase letters")
        else:
            strength_score += 20

        # Digits check
        if self.policy.require_digits and not re.search(r'\d', password):
            errors.append("Password must contain digits")
        else:
            strength_score += 20

        # Special chars check
        if self.policy.require_special_chars and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain special characters")
        else:
            strength_score += 20

        # History check
        if user_history and self.policy.prevent_reuse > 0:
            recent_passwords = user_history[:self.policy.prevent_reuse]
            for old_hash in recent_passwords:
                if verify_password(password, old_hash):
                    errors.append(f"Password cannot be reused. Last {self.policy.prevent_reuse} passwords are not allowed.")
                    strength_score -= 50
                    break

        return PasswordValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            strength_score=max(0, min(100, strength_score))
        )
```

#### Configuration

```python
# SecurityConfig
min_password_length: int = 12
require_uppercase: bool = True
require_lowercase: bool = True
require_digits: bool = True
require_special_chars: bool = True
prevent_password_reuse: int = 5
password_expiration_days: int = 90
```

#### Benefits

- Enforces strong passwords
- Prevents password reuse
- Improves overall security
- Reduces successful attacks

---

### 2.4 Session Security

**Goal:** Enhance session security and detect suspicious activity

#### Tasks

- [ ] Add session fingerprinting (device/browser fingerprint)
- [ ] Implement session timeout on inactivity
- [ ] Add concurrent session limits
- [ ] Implement session binding to IP address (optional)
- [ ] Add suspicious activity detection
- [ ] Create session management UI

#### Files to Create/Modify

**New Files:**

```
app/core/security/fingerprint.py
app/services/sessions/session_security.py
app/api/v1/users/sessions.py
```

**Modified Files:**

```
app/models/sessions.py (add fields)
app/services/sessions/session_services.py
app/core/config/security.py
```

#### Database Migration

```sql
ALTER TABLE sessions ADD COLUMN device_fingerprint VARCHAR(255) NULL;
ALTER TABLE sessions ADD COLUMN device_info JSONB DEFAULT '{}'::jsonb;
ALTER TABLE sessions ADD COLUMN suspicious_activities JSONB DEFAULT '[]'::jsonb;
```

#### Implementation Details

```python
# app/core/security/fingerprint.py
from hashlib import sha256
from user_agents import parse

def generate_device_fingerprint(
    user_agent: str,
    screen_resolution: str | None = None,
    timezone: str | None = None,
) -> str:
    """Generate a device fingerprint from request data."""
    ua = parse(user_agent)

    data = f"{ua.browser.family}{ua.os.family}{screen_resolution}{timezone}"

    return sha256(data.encode()).hexdigest()

# Session validation with fingerprint
async def validate_session_with_fingerprint(
    session_id: str,
    current_fingerprint: str,
) -> SessionValidationResult:
    session = await repo.get_by_session_id(session_id)

    if session.device_fingerprint != current_fingerprint:
        session.suspicious_activities.append({
            "type": "fingerprint_mismatch",
            "timestamp": datetime.now(UTC).isoformat(),
            "expected": session.device_fingerprint,
            "actual": current_fingerprint,
        })
        await repo.save()

        # Option 1: Require re-authentication
        # Option 2: Mark session as suspicious but allow
        # Option 3: Immediately revoke session

    return SessionValidationResult(...)
```

#### Configuration

```python
# SecurityConfig
max_concurrent_sessions: int = 3
inactivity_timeout_minutes: int = 30
bind_to_ip: bool = False
strict_fingerprinting: bool = True
auto_revoke_on_fingerprint_change: bool = False
```

#### Benefits

- Detects session hijacking
- Limits concurrent sessions
- Provides security insights
- Improves user control

---

### 2.5 Security Headers & CSP

**Goal:** Web security hardening through HTTP headers

#### Tasks

- [ ] Add security headers middleware
- [ ] Implement Content Security Policy
- [ ] Add HSTS header
- [ ] Implement CSRF protection for state-changing requests
- [ ] Add X-Frame-Options, X-Content-Type-Options
- [ ] Configure Referrer-Policy

#### Files to Create/Modify

**New Files:**

```
app/core/middleware/security_headers.py
app/core/middleware/csrf.py
```

**Modified Files:**

```
app/core/config/security.py (add CSP config)
app/main.py (add middleware)
```

#### Implementation Details

```python
# app/core/middleware/security_headers.py
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS (only in production with valid HTTPS)
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy
        csp = self._build_csp()
        response.headers["Content-Security-Policy"] = csp

        return response

    def _build_csp(self) -> str:
        policies = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
        ]
        return "; ".join(policies)

# app/core/middleware/csrf.py
from starlette.middleware.csrf import CSRFMiddleware

def add_csrf_protection(app: FastAPI):
    app.add_middleware(
        CSRFMiddleware,
        secret=settings.security.csrf_secret,
        cookie_name="csrf_token",
        cookie_secure=not settings.debug,
        cookie_httponly=True,
        cookie_samesite="strict",
    )
```

#### Configuration

```python
# SecurityConfig
enable_csp: bool = True
enable_hsts: bool = True
enable_csrf: bool = True
csp_report_uri: str | None = None
```

#### Benefits

- Prevents XSS attacks
- Prevents clickjacking
- Prevents CSRF attacks
- Improves security score

---

### Phase 2 Checkpoint

#### Deliverables

- [x] Rate limiting implemented
- [x] Account lockout working
- [x] Password policies enforced
- [x] Session security enhanced
- [x] Security headers configured
- [x] Security tests passing

#### Acceptance Criteria

- All security tests pass
- OWASP ZAP scan passes (no critical/high vulnerabilities)
- Rate limiting tested and verified
- Lockout tested and verified
- Password validation working
- No performance degradation (<10% overhead)

#### Testing Checklist

- [ ] Rate limit tests (various limits)
- [ ] Account lockout tests (progressive)
- [ ] Password validation tests (all policies)
- [ ] Session fingerprinting tests
- [ ] Security headers tests
- [ ] OWASP ZAP scan
- [ ] Performance benchmarks

---

## Phase 3: Feature Completeness

**Duration:** 4-5 days | **Risk:** Medium | **Impact:** High

### Overview

This phase focuses on adding essential authentication features to make the system production-ready and user-friendly.

### 3.1 Password Reset Flow

**Goal:** Enable secure password reset via email

#### Tasks

- [ ] Implement password reset token generation
- [ ] Create password reset email templates
- [ ] Add password reset request endpoint
- [ ] Implement password reset confirmation endpoint
- [ ] Add token expiration (15 min)
- [ ] Add rate limiting for reset requests
- [ ] Audit log password reset events
- [ ] Add reset token invalidation on use

#### Files to Create/Modify

**New Files:**

```
app/services/auth/password_reset.py
app/api/v1/auth/password_reset.py
app/schemas/auth/password_reset.py
app/templates/email/password_reset_request.html
app/templates/email/password_reset_success.html
```

**Modified Files:**

```
app/models/users.py (add fields)
app/services/email/email_service.py
app/core/settings.py (add URLs)
```

#### Database Migration

```sql
ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(255) UNIQUE NULL;
ALTER TABLE users ADD COLUMN password_reset_expires_at TIMESTAMP NULL;
```

#### Implementation Details

```python
# app/services/auth/password_reset.py
import secrets
from datetime import UTC, datetime, timedelta

class PasswordResetService:
    def __init__(self, user_repo: UserRepository, email_service: EmailService):
        self.user_repo = user_repo
        self.email_service = email_service

    async def request_password_reset(self, email: str) -> None:
        user = await self.user_repo.get_by_email(email)

        # Always return success to prevent email enumeration
        if not user:
            logger.info(f"Password reset requested for non-existent email: {email}")
            return

        # Generate secure token
        token = secrets.token_urlsafe(64)
        expires_at = datetime.now(UTC) + timedelta(minutes=15)

        # Store token
        user.password_reset_token = token
        user.password_reset_expires_at = expires_at
        await self.user_repo.save()

        # Send email
        reset_url = f"{settings.app.frontend_url}/reset-password?token={token}"
        await self.email_service.send_password_reset_email(
            user.email,
            reset_url,
            user.name
        )

        logger.info(f"Password reset token generated for user: {user.id}")

    async def reset_password(self, token: str, new_password: str) -> None:
        user = await self.user_repo.get_by_reset_token(token)

        if not user:
            raise InvalidTokenError()

        if user.password_reset_expires_at < datetime.now(UTC):
            raise TokenExpiredError()

        # Validate password
        validator = PasswordValidator(settings.security.password_policy)
        result = validator.validate(new_password, user.password_history)
        if not result.is_valid:
            raise PasswordValidationError(result.errors)

        # Update password
        user.hashed_password = hash_password(new_password)
        user.password_changed_at = datetime.now(UTC)
        user.password_history.append(hash_password(new_password))
        user.password_reset_token = None
        user.password_reset_expires_at = None
        await self.user_repo.save()

        # Send confirmation email
        await self.email_service.send_password_reset_success_email(user.email, user.name)

        logger.info(f"Password reset completed for user: {user.id}")
```

#### API Endpoints

```python
# app/api/v1/auth/password_reset.py
@router.post("/password-reset/request")
@rate_limit(times=3, seconds=3600)  # 3 attempts per hour
async def request_password_reset(
    request: PasswordResetRequest,
    service: PasswordResetService = Depends(get_password_reset_service),
):
    """Request a password reset email."""
    await service.request_password_reset(request.email)
    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/password-reset/confirm")
async def reset_password(
    request: PasswordResetConfirm,
    service: PasswordResetService = Depends(get_password_reset_service),
):
    """Reset password using token."""
    await service.reset_password(request.token, request.new_password)
    return {"message": "Password reset successful"}
```

#### Benefits

- Improved user experience
- Reduced support tickets
- Secure password recovery
- Compliant with security best practices

---

### 3.2 Email Verification

**Goal:** Verify user email addresses

#### Tasks

- [ ] Generate email verification tokens
- [ ] Create verification email templates
- [ ] Add verification endpoint
- [ ] Implement resend verification endpoint
- [ ] Add verification status to user model
- [ ] Block unverified users from certain actions
- [ ] Add verification reminder emails

#### Files to Create/Modify

**New Files:**

```
app/services/auth/email_verification.py
app/api/v1/auth/verification.py
app/schemas/auth/verification.py
app/templates/email/verify_email.html
app/templates/email/verification_reminder.html
```

**Modified Files:**

```
app/models/users.py (add fields)
app/services/email/email_service.py
```

#### Database Migration

```sql
ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN verification_token VARCHAR(255) UNIQUE NULL;
ALTER TABLE users ADD COLUMN verification_expires_at TIMESTAMP NULL;
ALTER TABLE users ADD COLUMN verification_reminders_sent INTEGER DEFAULT 0;
```

#### Implementation Details

```python
# app/services/auth/email_verification.py
class EmailVerificationService:
    def __init__(self, user_repo: UserRepository, email_service: EmailService):
        self.user_repo = user_repo
        self.email_service = email_service

    async def generate_verification(self, user: User) -> str:
        token = secrets.token_urlsafe(64)
        expires_at = datetime.now(UTC) + timedelta(days=7)

        user.verification_token = token
        user.verification_expires_at = expires_at
        await self.user_repo.save()

        verification_url = f"{settings.app.frontend_url}/verify-email?token={token}"
        await self.email_service.send_verification_email(
            user.email,
            verification_url,
            user.name
        )

        return token

    async def verify_email(self, token: str) -> None:
        user = await self.user_repo.get_by_verification_token(token)

        if not user:
            raise InvalidTokenError()

        if user.verification_expires_at < datetime.now(UTC):
            raise TokenExpiredError()

        user.is_verified = True
        user.verification_token = None
        user.verification_expires_at = None
        await self.user_repo.save()

        await self.email_service.send_welcome_email(user.email, user.name)
```

#### API Endpoints

```python
@router.post("/verify")
async def verify_email(
    token: str,
    service: EmailVerificationService = Depends(get_verification_service),
):
    """Verify email address using token."""
    await service.verify_email(token)
    return {"message": "Email verified successfully"}

@router.post("/verify/resend")
@rate_limit(times=3, seconds=3600)
async def resend_verification(
    request: ResendVerificationRequest,
    service: EmailVerificationService = Depends(get_verification_service),
):
    """Resend verification email."""
    await service.resend_verification(request.email)
    return {"message": "If the email exists, a verification link has been sent"}
```

#### Benefits

- Verified user base
- Reduced spam/fake accounts
- Improved email deliverability
- Compliant with regulations (GDPR)

---

### 3.3 User Registration Flow

**Goal:** Complete onboarding experience

#### Tasks

- [ ] Add user registration endpoint
- [ ] Implement email verification requirement
- [ ] Add welcome email
- [ ] Create user profile fields (optional)
- [ ] Implement CAPTCHA (optional)
- [ ] Add registration rate limiting
- [ ] Add terms of service acceptance
- [ ] Create registration validation

#### Files to Create/Modify

**New Files:**

```
app/services/auth/registration.py
app/api/v1/auth/register.py
app/schemas/auth/register.py
app/templates/email/welcome.html
```

**Modified Files:**

```
app/models/users.py (add profile fields)
app/services/email/email_service.py
app/core/security/captcha.py (optional)
```

#### Database Migration

```sql
ALTER TABLE users ADD COLUMN terms_accepted_at TIMESTAMP NULL;
ALTER TABLE users ADD COLUMN marketing_consent BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN phone VARCHAR(20) NULL;
ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500) NULL;
ALTER TABLE users ADD COLUMN bio TEXT NULL;
```

#### Implementation Details

```python
# app/services/auth/registration.py
class RegistrationService:
    def __init__(
        self,
        user_repo: UserRepository,
        email_service: EmailService,
        password_validator: PasswordValidator,
        verification_service: EmailVerificationService,
    ):
        self.user_repo = user_repo
        self.email_service = email_service
        self.password_validator = password_validator
        self.verification_service = verification_service

    async def register(self, data: RegistrationRequest) -> User:
        # Check if user exists
        if await self.user_repo.exists(username=data.username):
            raise UsernameAlreadyExistsError()

        if await self.user_repo.exists(email=data.email):
            raise EmailAlreadyExistsError()

        # Validate password
        password_result = self.password_validator.validate(data.password)
        if not password_result.is_valid:
            raise PasswordValidationError(password_result.errors)

        # Create user
        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
            name=data.name,
            terms_accepted_at=datetime.now(UTC),
            marketing_consent=data.marketing_consent,
            is_active=True,
            is_verified=False,
        )

        await self.user_repo.add(user)

        # Send verification email
        await self.verification_service.generate_verification(user)

        logger.info(f"New user registered: {user.id}")

        return user
```

#### API Endpoints

```python
@router.post("/register")
@rate_limit(times=5, seconds=3600)
async def register(
    request: RegistrationRequest,
    service: RegistrationService = Depends(get_registration_service),
):
    """Register a new user account."""
    user = await service.register(request)
    return {
        "message": "Registration successful. Please check your email to verify your account.",
        "user_id": user.id,
    }
```

#### Benefits

- Complete onboarding
- User-friendly registration
- Verified user base
- Legal compliance (ToS)

---

### 3.4 OAuth/OIDC Integration

**Goal:** Enable social login (optional, advanced)

#### Tasks

- [ ] Add OAuth configuration
- [ ] Implement OAuth flow (Google, GitHub, etc.)
- [ ] Create user profile linking
- [ ] Handle account merging
- [ ] Add OAuth tokens storage
- [ ] Implement token refresh for OAuth
- [ ] Create OAuth account management

#### Files to Create/Modify

**New Files:**

```
app/services/oauth/oauth_service.py
app/api/v1/auth/oauth.py
app/models/oauth.py (OAuthAccount model)
app/core/config/oauth.py
app/schemas/oauth.py
```

**Modified Files:**

```
app/models/users.py
pyproject.toml (add authlib or similar)
```

#### Database Migration

```sql
CREATE TABLE oauth_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP NULL,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    scope TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider, provider_user_id)
);

CREATE INDEX idx_oauth_accounts_user ON oauth_accounts(user_id);
CREATE INDEX idx_oauth_accounts_provider ON oauth_accounts(provider, provider_user_id);
```

#### Implementation Details

```python
# app/services/oauth/oauth_service.py
from authlib.integrations.starlette_client import OAuth

class OAuthService:
    def __init__(self, config: OAuthConfig):
        self.oauth = OAuth()
        self._register_providers(config)

    def _register_providers(self, config: OAuthConfig):
        if config.google_client_id:
            self.oauth.register(
                name='google',
                client_id=config.google_client_id,
                client_secret=config.google_client_secret,
                server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                client_kwargs={'scope': 'openid email profile'}
            )

        if config.github_client_id:
            self.oauth.register(
                name='github',
                client_id=config.github_client_id,
                client_secret=config.github_client_secret,
                server_metadata_url='https://api.github.com/.well-known/oauth-authorization-server',
                client_kwargs={'scope': 'user:email'}
            )

    async def handle_oauth_callback(
        self,
        provider: str,
        token: dict,
        user_info: dict,
    ) -> OAuthLoginResult:
        # Find or create user
        oauth_account = await self.oauth_repo.get_by_provider(
            provider,
            user_info['sub']
        )

        if oauth_account:
            # Existing user
            user = await self.user_repo.get_by_id(oauth_account.user_id)
            # Update tokens
            oauth_account.access_token = token['access_token']
            oauth_account.refresh_token = token.get('refresh_token')
            await self.oauth_repo.save()
        else:
            # New user
            user = await self._create_user_from_oauth(provider, user_info, token)
            oauth_account = await self._create_oauth_account(
                user.id,
                provider,
                user_info['sub'],
                token
            )

        # Generate auth tokens
        login_result = await self.auth_service.login(
            user,
            ip=request.client.host,
            ua=request.headers.get('user-agent')
        )

        return OAuthLoginResult(
            user=user,
            tokens=login_result,
            is_new_account=not oauth_account
        )
```

#### API Endpoints

```python
@router.get("/oauth/{provider}")
async def oauth_login(provider: str, request: Request):
    """Redirect to OAuth provider."""
    client = oauth_service.get_client(provider)
    redirect_uri = request.url_for('oauth_callback', provider=provider)
    return await client.authorize_redirect(request, redirect_uri)

@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    request: Request,
    service: OAuthService = Depends(get_oauth_service),
):
    """Handle OAuth callback."""
    token = await oauth_service.get_client(provider).authorize_access_token(request)
    user_info = await oauth_service.get_client(provider).parse_id_token(request, token)

    result = await service.handle_oauth_callback(provider, token, user_info)
    return result
```

#### Benefits

- Reduced friction for users
- Access to social profiles
- Improved conversion
- Modern authentication option

---

### 3.5 Two-Factor Authentication (2FA)

**Goal:** Add optional 2FA support

#### Tasks

- [ ] Implement TOTP (Time-based One-Time Password)
- [ ] Generate backup codes
- [ ] Add 2FA setup endpoint
- [ ] Add 2FA verification endpoint
- [ ] Create recovery flow
- [ ] Store 2FA secrets securely
- [ ] Add 2FA management UI endpoints

#### Files to Create/Modify

**New Files:**

```
app/services/auth/2fa.py
app/api/v1/auth/2fa.py
app/schemas/auth/2fa.py
app/core/utils/otp.py
```

**Modified Files:**

```
app/models/users.py (add 2fa fields)
pyproject.toml (add pyotp)
```

#### Database Migration

```sql
ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN two_factor_secret VARCHAR(255) UNIQUE NULL;
ALTER TABLE users ADD COLUMN two_factor_backup_codes JSONB DEFAULT '[]'::jsonb;
```

#### Implementation Details

```python
# app/services/auth/2fa.py
import pyotp
import qrcode
import io
import base64

class TwoFactorAuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def setup_2fa(self, user: User) -> Setup2FAResult:
        """Generate TOTP secret and QR code."""
        secret = pyotp.random_base32()

        # Store temporarily (not enabled yet)
        user.two_factor_secret = secret
        await self.user_repo.save()

        # Generate QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name=settings.app.name
        )

        qr_code = await self._generate_qr_code(provisioning_uri)

        return Setup2FAResult(
            secret=secret,
            qr_code=qr_code,
            backup_codes=await self._generate_backup_codes(secret)
        )

    async def enable_2fa(self, user: User, verification_code: str) -> None:
        """Enable 2FA after verification."""
        totp = pyotp.TOTP(user.two_factor_secret)

        if not totp.verify(verification_code):
            raise InvalidVerificationCodeError()

        user.two_factor_enabled = True
        await self.user_repo.save()

    async def verify_2fa(self, user: User, code: str) -> bool:
        """Verify 2FA code."""
        if not user.two_factor_enabled:
            return True  # 2FA not enabled, allow

        # Check TOTP
        totp = pyotp.TOTP(user.two_factor_secret)
        if totp.verify(code):
            return True

        # Check backup codes
        if code in user.two_factor_backup_codes:
            user.two_factor_backup_codes.remove(code)
            await self.user_repo.save()
            return True

        return False

    async def disable_2fa(self, user: User, password: str) -> None:
        """Disable 2FA."""
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.two_factor_backup_codes = []
        await self.user_repo.save()

    async def _generate_backup_codes(self, secret: str, count: int = 10) -> List[str]:
        """Generate backup codes."""
        codes = []
        for _ in range(count):
            code = secrets.token_urlsafe(8).upper()
            codes.append(code)
        return codes

    async def _generate_qr_code(self, uri: str) -> str:
        """Generate QR code as base64 image."""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"
```

#### API Endpoints

```python
@router.post("/2fa/setup")
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    service: TwoFactorAuthService = Depends(get_2fa_service),
):
    """Setup 2FA for user account."""
    result = await service.setup_2fa(current_user)
    return result

@router.post("/2fa/enable")
async def enable_2fa(
    request: Enable2FARequest,
    current_user: User = Depends(get_current_user),
    service: TwoFactorAuthService = Depends(get_2fa_service),
):
    """Enable 2FA after verification."""
    await service.enable_2fa(current_user, request.code)
    return {"message": "2FA enabled successfully"}

@router.post("/2fa/disable")
async def disable_2fa(
    request: Disable2FARequest,
    current_user: User = Depends(get_current_user),
    service: TwoFactorAuthService = Depends(get_2fa_service),
):
    """Disable 2FA."""
    await service.disable_2fa(current_user, request.password)
    return {"message": "2FA disabled successfully"}
```

#### Benefits

- Enhanced security
- Protection against password theft
- Compliance with security standards
- User control over security

---

### Phase 3 Checkpoint

#### Deliverables

- [x] Password reset flow complete
- [x] Email verification working
- [x] User registration complete
- [x] OAuth integrated (optional)
- [x] 2FA implemented (optional)
- [x] All feature tests passing

#### Acceptance Criteria

- User can reset password successfully
- Email verification works end-to-end
- Registration flow complete and tested
- OAuth login works (if implemented)
- 2FA setup and verify works (if implemented)
- All email templates tested
- Rate limiting on sensitive endpoints

#### Testing Checklist

- [ ] Password reset flow tests
- [ ] Email verification tests
- [ ] Registration flow tests
- [ ] OAuth integration tests (if applicable)
- [ ] 2FA setup/verify/disable tests
- [ ] Email delivery tests
- [ ] End-to-end user journey tests

---

## Phase 4: Performance & Scalability

**Duration:** 3-4 days | **Risk:** Medium | **Impact:** High

### Overview

This phase focuses on optimizing performance and preparing the system for high traffic loads.

### 4.1 Caching Layer

**Goal:** Reduce database queries and improve response times

#### Tasks

- [ ] Add Redis/Cache integration
- [ ] Cache user data (with invalidation)
- [ ] Cache session lookups
- [ ] Cache rate limiting counters
- [ ] Implement cache warming
- [ ] Add cache hit/miss metrics
- [ ] Configure cache eviction policies

#### Files to Create/Modify

**New Files:**

```
app/core/cache/cache_manager.py
app/core/cache/decorators.py
app/core/cache/keys.py
app/core/cache/config.py
```

**Modified Files:**

```
app/repositories/base.py (add caching)
app/services/auth/auth_services.py (add cache invalidation)
app/core/settings.py (add cache config)
pyproject.toml (add redis or cachetools)
```

#### Implementation Details

```python
# app/core/cache/cache_manager.py
from typing import Optional, Any
from functools import wraps
import json
import redis.asyncio as redis
from loguru import logger

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache with TTL."""
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")

    async def delete_pattern(self, pattern: str) -> None:
        """Delete keys matching pattern."""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")

    async def increment(self, key: str, ttl: int = 3600) -> int:
        """Increment counter and set TTL if new."""
        try:
            value = await self.redis.incr(key)
            if value == 1:
                await self.redis.expire(key, ttl)
            return value
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return 0

# app/core/cache/decorators.py
def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache_manager.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator
```

#### Cache Strategy

```python
# User Cache
USER_CACHE_TTL = 300  # 5 minutes
USER_CACHE_KEY_PREFIX = "user"

# Session Cache
SESSION_CACHE_TTL = 60  # 1 minute
SESSION_CACHE_KEY_PREFIX = "session"

# Rate Limit Cache
RATE_LIMIT_CACHE_TTL = 3600  # 1 hour
RATE_LIMIT_KEY_PREFIX = "ratelimit"

# Repository with caching
class CachedUserRepository(BaseRepository[User]):
    async def get_by_id(self, user_id: int) -> Optional[User]:
        cache_key = f"user:id:{user_id}"
        cached_user = await cache_manager.get(cache_key)

        if cached_user:
            return User(**cached_user)

        user = await super().get_by_id(user_id)
        if user:
            await cache_manager.set(cache_key, user.model_dump(), USER_CACHE_TTL)

        return user

    async def save(self) -> None:
        await super().save()
        # Invalidate user cache
        await cache_manager.delete_pattern("user:*")
```

#### Benefits

- Reduced database load
- Faster response times
- Better scalability
- Improved user experience

---

### 4.2 Database Optimization

**Goal:** Improve query performance

#### Tasks

- [ ] Add missing database indexes
- [ ] Optimize N+1 queries
- [ ] Implement query result pagination
- [ ] Add database connection pooling config
- [ ] Create database health checks
- [ ] Add query performance logging
- [ ] Analyze and optimize slow queries

#### Files to Create/Modify

**New Files:**

```
alembic/versions/xxx_add_indexes.py (migration)
app/database/pagination.py
app/database/metrics.py
```

**Modified Files:**

```
app/repositories/base.py (add pagination)
app/database/session.py (optimize pool settings)
app/core/middleware/query_logger.py
```

#### Database Indexes

```sql
-- Migration to add indexes

-- Sessions table
CREATE INDEX idx_sessions_user_expires ON sessions(user_id, expires_at);
CREATE INDEX idx_sessions_user_active ON sessions(user_id) WHERE is_revoked = FALSE;
CREATE INDEX idx_sessions_refresh_token ON sessions(refresh_token_hash);
CREATE INDEX idx_sessions_device_fingerprint ON sessions(device_fingerprint);

-- Users table
CREATE INDEX idx_users_username_active ON users(username, is_active);
CREATE INDEX idx_users_email_active ON users(email, is_active);
CREATE INDEX idx_users_locked ON users(locked_until) WHERE locked_until IS NOT NULL;
CREATE INDEX idx_users_verification ON users(verification_expires_at) WHERE verification_expires_at IS NOT NULL;
CREATE INDEX idx_users_reset_token ON users(password_reset_token) WHERE password_reset_token IS NOT NULL;

-- OAuth accounts
CREATE INDEX idx_oauth_provider ON oauth_accounts(provider, provider_user_id);
CREATE INDEX idx_oauth_user ON oauth_accounts(user_id);
```

#### Pagination Implementation

```python
# app/database/pagination.py
from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> 'PaginatedResponse[T]':
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

# Usage in repository
async def list_sessions(
    self,
    user_id: int,
    page: int = 1,
    page_size: int = 20
) -> PaginatedResponse[Session]:
    offset = (page - 1) * page_size

    # Get total count
    count_stmt = select(func.count()).select_from(Session).where(Session.user_id == user_id)
    total_result = await self.db.execute(count_stmt)
    total = total_result.scalar()

    # Get paginated items
    stmt = select(Session).where(Session.user_id == user_id).offset(offset).limit(page_size)
    result = await self.db.execute(stmt)
    items = list(result.scalars().all())

    return PaginatedResponse.create(items, total, page, page_size)
```

#### Connection Pool Configuration

```python
# app/database/session.py
class DatabaseSessionManager:
    def __init__(self, host: str, pool_config: PoolConfig):
        self.engine = create_async_engine(
            host,
            pool_size=pool_config.pool_size,
            max_overflow=pool_config.max_overflow,
            pool_timeout=pool_config.pool_timeout,
            pool_recycle=pool_config.pool_recycle,
            pool_pre_ping=True,
            echo=False,
        )
```

```python
# Configuration
class PoolConfig(BaseSettings):
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 1 hour
```

#### Benefits

- Faster queries
- Better database performance
- Reduced resource usage
- Improved scalability

---

### 4.3 Background Jobs

**Goal:** Offload non-critical tasks

#### Tasks

- [ ] Implement background job queue (Celery or Dramatiq)
- [ ] Clean expired sessions periodically
- [ ] Clean up rate limit counters
- [ ] Send emails asynchronously
- [ ] Generate analytics reports
- [ ] Archive old logs
- [ ] Add job monitoring

#### Files to Create/Modify

**New Files:**

```
app/workers/cleanup.py
app/workers/email.py
app/workers/analytics.py
app/workers/notifications.py
app/queue/queue_manager.py
app/queue/tasks.py
app/core/config/queue.py
```

**Modified Files:**

```
app/services/email/email_service.py
app/main.py (add worker startup)
pyproject.toml (add dramatiq or celery)
```

#### Implementation Details

```python
# app/queue/queue_manager.py
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import TimeLimit, Retry

broker = RedisBroker()
broker.add_middleware(TimeLimit(limit=60_000))  # 60 second limit
broker.add_middleware(Retry(max_retries=3))

dramatiq.set_broker(broker)

# app/workers/cleanup.py
import dramatiq
from datetime import UTC, datetime, timedelta

@dramatiq.actor
def cleanup_expired_sessions():
    """Clean up expired sessions older than 30 days."""
    from app.database.session import sessionmanager
    from app.models.sessions import Session
    from sqlalchemy import delete

    cutoff_date = datetime.now(UTC) - timedelta(days=30)

    with sessionmanager.session() as session:
        stmt = delete(Session).where(
            Session.expires_at < cutoff_date,
            Session.is_revoked == True
        )
        session.execute(stmt)
        session.commit()

    logger.info(f"Cleaned up expired sessions before {cutoff_date}")

@dramatiq.actor(schedule=dramatiq.cron("0 2 * * *"))  # Run at 2 AM daily
def cleanup_rate_limit_counters():
    """Clean up rate limit counters."""
    from app.core.cache.cache_manager import cache_manager

    await cache_manager.delete_pattern("ratelimit:*")

    logger.info("Cleaned up rate limit counters")

# app/workers/email.py
@dramatiq.actor
def send_password_reset_email(user_email: str, reset_url: str, user_name: str):
    """Send password reset email."""
    from app.services.email.email_service import EmailService

    email_service = EmailService()
    email_service.send_password_reset_email(user_email, reset_url, user_name)

# Usage in service
class PasswordResetService:
    async def request_password_reset(self, email: str) -> None:
        user = await self.user_repo.get_by_email(email)
        if not user:
            return

        token = secrets.token_urlsafe(64)
        expires_at = datetime.now(UTC) + timedelta(minutes=15)

        user.password_reset_token = token
        user.password_reset_expires_at = expires_at
        await self.user_repo.save()

        reset_url = f"{settings.app.frontend_url}/reset-password?token={token}"

        # Send email asynchronously
        send_password_reset_email.send(user.email, reset_url, user.name)

        logger.info(f"Password reset email queued for user: {user.id}")
```

#### Monitoring

```python
# Add worker monitoring
from dramatiq.middleware import Prometheus

broker.add_middleware(Prometheus())

# Or custom metrics
@dramatiq.actor
def monitored_task():
    from prometheus_client import Counter

    task_counter = Counter('tasks_completed_total', 'Total tasks completed', ['task_name'])
    task_counter.labels(task_name='cleanup_expired_sessions').inc()
```

#### Benefits

- Faster API responses
- Better resource utilization
- Asynchronous processing
- Improved reliability

---

### 4.4 Metrics & Monitoring

**Goal:** Observability and alerting

#### Tasks

- [ ] Add Prometheus metrics
- [ ] Track auth events (login, logout, failed attempts)
- [ ] Monitor system health
- [ ] Add performance metrics (response times, cache hit rates)
- [ ] Create Grafana dashboards
- [ ] Set up alerting rules
- [ ] Add distributed tracing

#### Files to Create/Modify

**New Files:**

```
app/core/metrics/prometheus.py
app/core/middleware/metrics.py
app/core/metrics/auth_metrics.py
app/core/metrics/cache_metrics.py
monitoring/dashboards/auth_dashboard.json
monitoring/dashboards/performance_dashboard.json
monitoring/alerts/alert_rules.yaml
```

**Modified Files:**

```
app/services/auth/auth_services.py (add metrics)
app/main.py (add metrics endpoint)
pyproject.toml (add prometheus-fastapi-instrumentator)
```

#### Implementation Details

```python
# app/core/metrics/prometheus.py
from prometheus_client import Counter, Histogram, Gauge, Summary
from functools import wraps
from typing import Callable
import time

# Auth metrics
auth_login_attempts = Counter(
    'auth_login_attempts_total',
    'Total login attempts',
    ['status']  # success, failure
)

auth_token_refreshes = Counter(
    'auth_token_refreshes_total',
    'Total token refreshes',
    ['status']
)

auth_active_sessions = Gauge(
    'auth_active_sessions',
    'Number of active sessions'
)

# Performance metrics
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint', 'status']
)

query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['table', 'operation']
)

# Cache metrics
cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# Middleware
def track_request_duration(func: Callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            # Track metrics here
            pass
    return wrapper

# Usage in auth service
class AuthService:
    async def login(self, user: User, ip: str = None, ua: str = None) -> LoginResponse:
        try:
            result = await self._perform_login(user, ip, ua)
            auth_login_attempts.labels(status='success').inc()
            return result
        except Exception as e:
            auth_login_attempts.labels(status='failure').inc()
            raise
```

#### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Auth System Dashboard",
    "panels": [
      {
        "title": "Login Rate",
        "targets": [
          {
            "expr": "rate(auth_login_attempts_total[5m])",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "Active Sessions",
        "targets": [
          {
            "expr": "auth_active_sessions"
          }
        ]
      },
      {
        "title": "Request Duration",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))"
          }
        ]
      }
    ]
  }
}
```

#### Alerting Rules

```yaml
# monitoring/alerts/alert_rules.yaml
groups:
  - name: auth_alerts
    rules:
      - alert: HighLoginFailureRate
        expr: rate(auth_login_attempts_total{status="failure"}[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High login failure rate detected"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 1
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "95th percentile response time is high"

      - alert: LowCacheHitRate
        expr: rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) < 0.5
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Cache hit rate is below 50%"

      - alert: DatabaseConnectionPoolExhausted
        expr: db_pool_active_connections / db_pool_max_connections > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearly exhausted"
```

#### Benefits

- Real-time visibility
- Proactive issue detection
- Performance insights
- Capacity planning

---

### 4.5 Connection Pooling & Scaling

**Goal:** Prepare for high load

#### Tasks

- [ ] Optimize database connection pool
- [ ] Implement HTTP connection pooling
- [ ] Add load balancing support
- [ ] Implement request queueing
- [ ] Add health check endpoints
- [ ] Create scaling playbook

#### Files to Create/Modify

**New Files:**

```
docs/scaling.md
docs/deployment.md
scripts/scale_up.sh
scripts/scale_down.sh
```

**Modified Files:**

```
app/database/session.py (optimize pool)
app/core/utils/httpx_factory.py (add pooling)
app/api/v1/health.py (enhance)
```

#### Implementation Details

```python
# app/database/session.py
class DatabaseSessionManager:
    def __init__(self, host: str, pool_config: PoolConfig):
        self.engine = create_async_engine(
            host,
            pool_size=pool_config.pool_size,
            max_overflow=pool_config.max_overflow,
            pool_timeout=pool_config.pool_timeout,
            pool_recycle=pool_config.pool_recycle,
            pool_pre_ping=True,
            echo=False,
        )

        self._sessionmaker = async_sessionmaker(
            bind=self.engine,
            autocommit=False,
            expire_on_commit=False,
            class_=AsyncSession,
        )

# app/core/utils/httpx_factory.py
import httpx
from httpx import Limits, Timeout

def create_async_client(config: HttpxConfig) -> httpx.AsyncClient:
    """Create optimized HTTP client with pooling."""
    limits = Limits(
        max_connections=config.max_connections,
        max_keepalive_connections=config.max_keepalive,
    )

    timeout = Timeout(
        timeout=config.timeout_seconds,
        connect=10.0,
    )

    return httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        retries=config.retries,
    )

# app/api/v1/health.py
from fastapi import APIRouter
from datetime import datetime, UTC

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat()
    }

@router.get("/ready")
async def readiness_check():
    """Readiness check."""
    checks = {
        "database": await check_database(),
        "cache": await check_cache(),
        "redis": await check_redis(),
    }

    all_healthy = all(checks.values())

    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat()
    }

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

#### Configuration

```python
# PoolConfig
pool_size: int = 20
max_overflow: int = 10
pool_timeout: int = 30
pool_recycle: int = 3600  # 1 hour

# HttpxConfig
max_connections: int = 100
max_keepalive_connections: int = 20
timeout_seconds: float = 10.0
retries: int = 3
```

#### Benefits

- Handle high traffic
- Better resource utilization
- Improved reliability
- Easier scaling

---

### Phase 4 Checkpoint

#### Deliverables

- [x] Caching implemented
- [x] Database optimized
- [x] Background jobs running
- [x] Metrics collecting
- [x] Monitoring configured
- [x] Performance tests passing

#### Acceptance Criteria

- Cache hit rate > 80%
- Query time < 100ms (95th percentile)
- Auth endpoints < 200ms response time
- Can handle 1000+ requests/second
- Metrics visible in Grafana
- Background jobs running reliably
- Health checks passing

#### Testing Checklist

- [ ] Load testing (1000+ rps)
- [ ] Cache performance tests
- [ ] Database query optimization tests
- [ ] Background job reliability tests
- [ ] Metrics accuracy tests
- [ ] Failover tests

---

## Implementation Order & Dependencies

```
Phase 1 (Foundation)
├── Must complete before Phase 2
├── Must complete before Phase 4
├── Independent from Phase 3
└── Estimated: 2-3 days

Phase 2 (Security)
├── Can start after Phase 1
├── Must complete before Phase 3
├── Independent from Phase 4
└── Estimated: 3-4 days

Phase 3 (Features)
├── Can start after Phase 2
├── Independent from Phase 4
├── Can run parallel to Phase 4
└── Estimated: 4-5 days

Phase 4 (Performance)
├── Can start after Phase 1
├── Can run parallel to Phase 3
├── Depends on Phase 1 architecture
└── Estimated: 3-4 days
```

### Parallel Execution Options

**Option 1: Sequential (Recommended)**

```
Phase 1 → Phase 2 → Phase 3 → Phase 4
Total: 12-16 days
```

**Option 2: Parallel Phase 3 & 4**

```
Phase 1 → Phase 2 → (Phase 3 + Phase 4)
Total: 10-13 days
```

**Option 3: Fast Track (Feature Flags)**

```
Phase 1 → Phase 2 → Phase 3 (critical features only) → Phase 4
Phase 3 (optional features) can be done later
```

---

## Risk Mitigation

### High Risk Areas

#### 1. Database Migrations

**Risk:** Breaking changes, data loss
**Mitigation:**

- Test migrations in staging environment first
- Create rollback scripts for all migrations
- Backup database before production migration
- Use feature flags for new functionality
- Run migrations during low-traffic periods

#### 2. Caching Invalidation

**Risk:** Stale data, inconsistent state
**Mitigation:**

- Start with conservative TTLs (5 minutes)
- Implement cache versioning
- Add cache warming strategies
- Monitor cache hit/miss ratios
- Implement cache flush mechanisms
- Add alerts for low cache hit rates

#### 3. Background Jobs

**Risk:** Failed jobs, lost tasks
**Mitigation:**

- Add monitoring and alerts for failed jobs
- Implement retry logic with exponential backoff
- Use persistent job queues
- Add dead letter queue for failed jobs
- Monitor job queue depth
- Add circuit breakers for dependent services

#### 4. OAuth Integration

**Risk:** Security vulnerabilities, token leaks
**Mitigation:**

- Implement in feature branch first
- Security review before merge
- Use well-tested libraries (authlib)
- Encrypt stored tokens
- Implement token rotation
- Add monitoring for OAuth flows

### Rollback Plan

#### Database Rollback

```bash
# Rollback migration
alembic downgrade -1

# Or to specific version
alembic downgrade <revision>
```

#### Feature Flags

```python
# Disable new features via environment variables
FEATURE_RATE_LIMITING=false
FEATURE_ACCOUNT_LOCKOUT=false
FEATURE_PASSWORD_RESET=false
```

#### Configuration Rollback

```python
# Use old configuration values
# Keep old code paths commented out
# Can quickly switch back if issues arise
```

### Testing Strategy

#### Unit Tests

- Cover all new functionality
- Mock external dependencies
- Test edge cases

#### Integration Tests

- Test component interactions
- Test with real database
- Test cache layer

#### End-to-End Tests

- Test complete user journeys
- Test with staging environment
- Load testing

#### Security Tests

- OWASP ZAP scan
- SQL injection tests
- XSS tests
- CSRF tests

---

## Success Metrics

### Before Refactoring (Baseline)

| Metric | Current Value |
|--------|---------------|
| Auth endpoint response time | ~200ms |
| Database queries per login | ~5 |
| Test coverage | ~70% |
| Cache hit rate | N/A |
| Max concurrent users | Unknown |
| Security vulnerabilities | Basic auth only |
| API response time (95th percentile) | ~300ms |
| Failed login rate | Unknown |
| Session creation time | ~50ms |

### After Refactoring (Target)

| Metric | Target Value | Improvement |
|--------|--------------|-------------|
| Auth endpoint response time | <100ms | 50% faster |
| Database queries per login | ~2 (with cache) | 60% reduction |
| Test coverage | >90% | +20% |
| Cache hit rate | >80% | New metric |
| Max concurrent users | 10,000+ | New capability |
| Security vulnerabilities | OWASP Top 10 addressed | Complete hardening |
| API response time (95th percentile) | <200ms | 33% faster |
| Failed login rate | <5% | New metric |
| Session creation time | <20ms | 60% faster |

### Business Impact

**User Experience:**

- Faster page loads
- Fewer errors
- Better security
- More features

**Operational:**

- Better observability
- Easier debugging
- Improved reliability
- Faster incident response

**Development:**

- Easier to add features
- Better code quality
- Faster development
- Reduced technical debt

---

## Conclusion

This refactoring plan provides a comprehensive roadmap for transforming the authentication system from a basic implementation to a production-ready, secure, and scalable solution. The phased approach with checkpoints ensures:

1. **Progressive delivery** - Value delivered at each phase
2. **Risk management** - Each phase can be independently tested and rolled back
3. **Team alignment** - Clear milestones and deliverables
4. **Quality assurance** - Acceptance criteria for each phase

### Next Steps

1. Review and approve this plan
2. Assign resources and timelines
3. Set up staging environment
4. Begin Phase 1 implementation
5. Execute checkpoints after each phase

### Questions to Address

- Which phases are must-have vs. nice-to-have?
- What is the timeline for each phase?
- Who are the key stakeholders?
- What is the testing environment setup?
- What are the deployment procedures?

---

## Appendix

### A. File Structure Overview

```
backend/
├── app/
│   ├── api/
│   │   ├── containers.py (NEW)
│   │   ├── deps.py (MODIFIED)
│   │   └── v1/
│   │       ├── auth.py (MODIFIED)
│   │       ├── register.py (NEW)
│   │       ├── password_reset.py (NEW)
│   │       ├── verification.py (NEW)
│   │       ├── 2fa.py (NEW)
│   │       └── oauth.py (NEW)
│   ├── core/
│   │   ├── cache/
│   │   │   ├── cache_manager.py (NEW)
│   │   │   └── decorators.py (NEW)
│   │   ├── config/
│   │   │   ├── auth.py (NEW)
│   │   │   ├── security.py (NEW)
│   │   │   ├── feature_flags.py (NEW)
│   │   │   ├── database.py (NEW)
│   │   │   └── oauth.py (NEW)
│   │   ├── security/
│   │   │   ├── rate_limiter.py (NEW)
│   │   │   ├── fingerprint.py (NEW)
│   │   │   ├── password_validator.py (NEW)
│   │   │   └── 2fa.py (NEW)
│   │   └── metrics/
│   │       └── prometheus.py (NEW)
│   ├── repositories/
│   │   ├── base.py (NEW)
│   │   ├── users_repositories.py (MODIFIED)
│   │   └── sessions_repo.py (MODIFIED)
│   ├── services/
│   │   ├── base.py (NEW)
│   │   ├── auth/
│   │   │   ├── auth_services.py (MODIFIED)
│   │   │   ├── password_reset.py (NEW)
│   │   │   ├── email_verification.py (NEW)
│   │   ├── 2fa.py (NEW)
│   │   ├── oauth/
│   │   │   └── oauth_service.py (NEW)
│   │   └── email/
│   │       └── email_service.py (NEW)
│   ├── workers/
│   │   ├── cleanup.py (NEW)
│   │   └── email.py (NEW)
│   └── models/
│       ├── users.py (MODIFIED)
│       ├── sessions.py (MODIFIED)
│       └── oauth.py (NEW)
├── docs/
│   ├── architecture.md (NEW)
│   ├── auth_flow.md (NEW)
│   ├── api_reference.md (NEW)
│   ├── scaling.md (NEW)
│   └── deployment.md (NEW)
├── monitoring/
│   └── dashboards/ (NEW)
└── tests/
    ├── integration/
    ├── unit/
    └── e2e/
```

### B. Recommended Tools & Libraries

**Phase 1:**

- pydantic-settings (already used)
- dependency-injector (optional)

**Phase 2:**

- slowapi or fastapi-limiter (rate limiting)
- pyotp (2FA)
- user-agents (fingerprinting)

**Phase 3:**

- authlib (OAuth)
- pyotp (2FA)
- jinja2 (email templates)

**Phase 4:**

- redis (caching)
- dramatiq (background jobs)
- prometheus-client (metrics)
- prometheus-fastapi-instrumentator (auto-metrics)

### C. Configuration Examples

```python
# .env.example
APP_NAME=mkit-indosat-voucher-service
APP_VERSION=0.1.0
DEBUG=False

# Database
DB_URL=postgresql+asyncpg://user:pass@localhost/dbname

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10
JWT_REFRESH_TOKEN_EXPIRE_MINUTES=10080

# Security
SECURITY_LOGIN_ATTEMPTS_PER_MINUTE=5
SECURITY_REFRESH_ATTEMPTS_PER_MINUTE=10
SECURITY_MIN_PASSWORD_LENGTH=12
SECURITY_MAX_CONCURRENT_SESSIONS=3
SECURITY_INACTIVITY_TIMEOUT_MINUTES=30

# Cache
CACHE_URL=redis://localhost:6379/0
CACHE_USER_TTL=300
CACHE_SESSION_TTL=60

# OAuth
OAUTH_GOOGLE_CLIENT_ID=
OAUTH_GOOGLE_CLIENT_SECRET=
OAUTH_GITHUB_CLIENT_ID=
OAUTH_GITHUB_CLIENT_SECRET=

# Feature Flags
FEATURE_RATE_LIMITING=true
FEATURE_ACCOUNT_LOCKOUT=true
FEATURE_PASSWORD_RESET=true
FEATURE_EMAIL_VERIFICATION=true
FEATURE_2FA=false
FEATURE_OAUTH=false

# Queue
QUEUE_REDIS_URL=redis://localhost:6379/1
```

---

**Document Version:** 1.0
**Last Updated:** 2026-02-08
**Author:** Hasan Maki
**Status:** Ready for Review
