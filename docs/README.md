# DARI Wallet Backend Documentation

This folder contains all the documentation for the DARI Wallet backend project.

## Documentation Files

### API Documentation
- **BACKEND_API_SPECIFICATION.md** - Complete API specification with all 42 endpoints
- **ENDPOINT_CHANGES.md** - Summary of endpoint changes during refactoring

### Refactoring Documentation
- **BACKEND_REFACTORING_ANALYSIS.md** - Analysis of the refactoring process
- **BACKEND_REFACTORING_PLAN.md** - Detailed refactoring plan
- **REFACTORING_COMPLETE.md** - Completion summary and final status

### Feature Documentation
- **TRANSACTION_UPDATES.md** - Transaction system updates (fees, gasless transactions)
- **progress.md** - Development progress tracking

## Key Features

### Authentication & Users
- Email + OTP based authentication (no admin functionality)
- User registration, login, password reset flows
- KYC verification system
- Wallet management

### Transactions
- **Gasless Transactions**: DARI pays blockchain gas fees (~$0.0003/txn)
- **Platform Fees**: 1% domestic, 2% international (min $0.10, max $50, free <$1)
- **Multiple Transfer Methods**: 
  - Wallet address (0x...)
  - DARI username (@dari)
  - Phone number (+xxx)
- **Country Tracking**: ISO 3166-1 alpha-2 codes for fee calculation

### Supported Tokens
- USDC (Primary)
- MATIC (Native token)

### Additional Features
- QR code generation for payments
- Address resolver (@dari usernames)
- Transaction history and receipts
- Notification system
