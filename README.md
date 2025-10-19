# DARI Wallet V2 - FastAPI Backend

A production-ready FastAPI backend for DARI Wallet V2, a semi-custodial, real-time crypto wallet system supporting USDC and USDT on Polygon.

## 🚀 Features

### User Management
- **Registration & Authentication**: Email, mobile, and password-based registration with JWT authentication
- **KYC Verification**: Complete KYC process with document uploads and admin approval
- **PIN Security**: PIN-based transaction authorization
- **OTP Support**: Email and SMS-based OTP verification
- **Role-based Access**: User, Admin, SuperAdmin, and Support roles

### Wallet & Blockchain
- **Polygon Integration**: Native support for Polygon mainnet and Mumbai testnet
- **Multi-token Support**: USDC and USDT token management
- **Real-time Balances**: On-chain balance synchronization
- **Secure Key Management**: AES-encrypted private key storage
- **Transaction Management**: Send, receive, and track transactions with gas fee handling

### Security & Compliance
- **Encryption**: AES encryption for sensitive data
- **Audit Logging**: Comprehensive logging for all user and admin actions
- **Rate Limiting**: Built-in rate limiting and input validation
- **Fraud Detection**: Basic risk scoring and suspicious activity detection
- **Terms & Conditions**: Required acceptance during registration

### Admin Panel
- **User Management**: View, activate/deactivate users
- **KYC Management**: Approve/reject KYC requests with detailed review
- **Transaction Monitoring**: Monitor all transactions with risk assessment
- **System Configuration**: Manage tokens, currencies, and system settings
- **Analytics**: User statistics and transaction analytics

### Currency & Pricing
- **Multi-currency Support**: INR, USD, EUR, GBP, and more
- **Real-time Pricing**: CoinGecko API integration with 5-minute updates
- **Fiat Conversion**: Convert crypto balances to user's preferred currency

## 🛠 Tech Stack

- **Backend**: FastAPI 0.104+ with Python 3.11+
- **Database**: PostgreSQL 15+ with SQLAlchemy ORM
- **Caching**: Redis for session management and caching
- **Background Tasks**: Celery with Redis broker
- **Blockchain**: Web3.py for Polygon interaction
- **Authentication**: JWT with bcrypt password hashing
- **Email**: SMTP with HTML template support
- **SMS**: Twilio integration for OTP delivery
- **Monitoring**: Flower for Celery task monitoring
- **Documentation**: Auto-generated OpenAPI/Swagger docs

## � Project Structure

```
DARI V2/
├── app/                        # Main application package
│   ├── api/                    # API routes
│   │   └── v1/                 # API v1 endpoints
│   ├── core/                   # Core configurations
│   │   ├── config.py           # Settings and environment
│   │   ├── database.py         # Database connection
│   │   ├── security.py         # JWT and authentication
│   │   └── password.py         # Password hashing utilities
│   ├── crud/                   # Database operations
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic services
│   └── tasks/                  # Celery background tasks
├── alembic/                    # Database migrations
│   └── versions/               # Migration files
├── database/                   # Database setup files
│   ├── setup_database.sql      # Initial schema
│   └── README.md               # Database documentation
├── docs/                       # Project documentation
│   ├── BACKEND_API_SPECIFICATION.md
│   ├── ENDPOINT_CHANGES.md
│   └── README.md
├── scripts/                    # Utility scripts
│   └── init_db.py              # Database initialization
├── tests/                      # Test files
├── .env.example                # Environment template
├── alembic.ini                 # Alembic configuration
├── docker-compose.yml          # Docker development setup
├── docker-compose.prod.yml     # Docker production setup
├── Dockerfile                  # Docker image definition
├── requirements.txt            # Python dependencies
├── render.yaml                 # Render deployment config
├── setup_relayer.py            # Relayer wallet setup
└── README.md                   # This file
```

## �📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone and Setup**:
```bash
git clone <repository-url>
cd "DARI V2"
cp .env.example .env
```

2. **Configure Environment**:
Edit `.env` file with your configuration:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://dari_user:dari_password@localhost:5432/dari_wallet_v2

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ENCRYPTION_KEY=your-32-byte-encryption-key-change-in-production

# Email Configuration
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Blockchain
USE_TESTNET=true  # Set to false for production
```

3. **Start Services**:
```bash
docker-compose up -d
```

4. **Initialize Database**:
```bash
docker-compose exec api python scripts/init_db.py
```

### Manual Setup

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Setup Database**:
```bash
# Start PostgreSQL and Redis
# Update .env with your database credentials

# Initialize database
python scripts/init_db.py

# Run migrations
alembic upgrade head
```

3. **Start Services**:
```bash
# Start FastAPI server
# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 🚨 EMERGENCY RESTART (if server hangs)
python emergency_restart.py

# Start Celery worker (in another terminal)
celery -A app.celery_app worker --loglevel=info

# Start Celery beat scheduler (in another terminal)
celery -A app.celery_app beat --loglevel=info

# Start Flower monitoring (optional)
celery -A app.celery_app flower --port=5555
```

## 📖 API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `SECRET_KEY` | JWT secret key | Required |
| `ENCRYPTION_KEY` | AES encryption key | Required |
| `USE_TESTNET` | Use Mumbai testnet | `true` |
| `OTP_EMAIL_ENABLED` | Enable email OTP | `true` |
| `OTP_SMS_ENABLED` | Enable SMS OTP | `false` |
| `SMTP_HOST` | SMTP server host | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USERNAME` | SMTP username | Required |
| `SMTP_PASSWORD` | SMTP password | Required |

### Blockchain Configuration

The system supports both Polygon mainnet and Mumbai testnet:

**Mainnet** (Production):
- USDC: `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174`
- USDT: `0xc2132D05D31c914a87C6611C10748AEb04B58e8F`

**Mumbai Testnet** (Development):
- USDC: `0x9999f7Fea5938fD3b1E26A12c3f2fb024e194f97`
- USDT: `0xBD21A10F619BE90d6066c941b04e4B3B9b3d7ED1`

## 📊 Database Schema

### Core Tables

- **users**: User accounts with authentication and profile data
- **kyc_requests**: KYC submissions with document storage
- **wallets**: Blockchain wallets with encrypted private keys
- **tokens**: Supported tokens (USDC, USDT)
- **token_balances**: User token balances
- **transactions**: Transaction history with blockchain data
- **login_logs**: Authentication and security logs
- **admin_logs**: Admin action audit trail

## 🔒 Security Features

### Authentication & Authorization
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- PIN verification for transactions
- OTP verification for sensitive operations

### Data Security
- AES encryption for private keys
- Bcrypt password hashing
- Input validation and sanitization
- Rate limiting and DDoS protection

### Audit & Compliance
- Comprehensive audit logging
- Transaction risk scoring
- Suspicious activity detection
- Terms & conditions enforcement

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py -v
```

## 📈 Monitoring

### Celery Tasks (Flower)
Access Flower dashboard: http://localhost:5555

### Background Tasks
- **Price Updates**: Token prices updated every 5 minutes
- **Transaction Monitoring**: Pending transaction status checks
- **Email Notifications**: Async email delivery
- **Balance Updates**: Wallet balance synchronization

## 🚀 Deployment

### Production Checklist

1. **Environment Configuration**:
   - Set `USE_TESTNET=false`
   - Configure mainnet RPC URLs
   - Update contract addresses
   - Set strong encryption keys

2. **Security Hardening**:
   - Enable HTTPS/TLS
   - Configure firewall rules
   - Set up monitoring and alerting
   - Regular security updates

3. **Database Optimization**:
   - Configure connection pooling
   - Set up read replicas
   - Enable backup automation
   - Monitor performance

4. **Scaling Considerations**:
   - Load balancer setup
   - Multiple Celery workers
   - Redis clustering
   - Database sharding

### Docker Production Deployment

```bash
# Build production image
docker build -t dari-wallet-v2:latest .

# Deploy with production compose
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/change-password` - Change password
- `POST /api/v1/auth/set-pin` - Set transaction PIN

### KYC Management
- `POST /api/v1/kyc/submit` - Submit KYC documents
- `GET /api/v1/kyc/status` - Get KYC status
- `POST /api/v1/kyc/upload-document` - Upload KYC document

### Wallet Operations
- `GET /api/v1/wallets/` - Get user wallet
- `GET /api/v1/wallets/balance` - Get wallet balances
- `GET /api/v1/wallets/qr-code` - Generate QR code

### Transactions
- `POST /api/v1/transactions/send` - Send transaction
- `GET /api/v1/transactions/` - Get transaction history
- `GET /api/v1/transactions/{id}` - Get transaction details

### Admin Operations
- `GET /api/v1/admin/users` - List all users
- `GET /api/v1/admin/kyc/pending` - Pending KYC requests
- `POST /api/v1/admin/kyc/{id}/approve` - Approve KYC
- `POST /api/v1/admin/kyc/{id}/reject` - Reject KYC
- `GET /api/v1/admin/transactions/all` - Get all user transactions with filtering
- `POST /api/v1/admin/transactions/monitor` - Monitor transactions with advanced filtering

## 🚨 Troubleshooting

### Server Performance Issues

If the server becomes unresponsive or hangs on requests:

1. **Emergency Restart**:
```bash
python emergency_restart.py
```

2. **Check Database Connections**:
```bash
# Check for hanging connections
psql -h localhost -U dariwallettest -d dariwallet_v2 -c "SELECT pid, state, state_change FROM pg_stat_activity WHERE datname = 'dariwallet_v2';"

# Terminate hanging connections
psql -h localhost -U dariwallettest -d dariwallet_v2 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'dariwallet_v2' AND state = 'idle in transaction';"
```

3. **Performance Monitoring**:
```bash
# Check server logs for slow queries
tail -f logs/app.log | grep "slow"

# Monitor database performance
psql -h localhost -U dariwallettest -d dariwallet_v2 -c "SELECT query, state, query_start FROM pg_stat_activity WHERE state != 'idle';"
```

### Common Issues

- **Database Timeouts**: Server uses 5-second query timeouts to prevent hanging
- **Authentication Caching**: User authentication is cached for 5 minutes to reduce DB load
- **Admin Endpoint Caching**: Admin statistics cached for 5-15 minutes
- **Connection Pooling**: Limited to 5 connections with 10 overflow to prevent resource exhaustion

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🆘 Support

For support and questions:
- Email: support@dariwallet.com
- Documentation: [API Docs](http://localhost:8000/docs)
- Issues: [GitHub Issues](https://github.com/your-repo/issues)

---

**DARI Wallet V2** - Secure, scalable, and production-ready crypto wallet backend.
