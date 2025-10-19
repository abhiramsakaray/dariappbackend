# KYC Verified Data Endpoint

## Overview
Added a new endpoint to retrieve verified KYC data including user information, document details, and selfie image.

## Endpoint Details

### GET `/api/v1/kyc/verified-data`

**Authentication Required:** Yes (Bearer token)

**Description:** Returns complete KYC verification data for the authenticated user, including profile information, document details, and image URLs.

### Response Format

```json
{
  "user_id": 1,
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "kyc_verified": true,
  "kyc_details": {
    "id": 5,
    "status": "APPROVED",
    "full_name": "John Doe",
    "date_of_birth": "1990-01-15",
    "nationality": "United States",
    "address_line_1": "123 Main Street",
    "address_line_2": "Apt 4B",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "United States",
    "document_type": "PASSPORT",
    "document_number": "A12345678",
    "submitted_at": "2024-01-15T10:30:00Z",
    "reviewed_at": "2024-01-15T15:45:00Z"
  },
  "files": {
    "selfie": {
      "file_id": 10,
      "filename": "selfie_20240115.jpg",
      "file_path": "uploads/user_1/selfie_20240115.jpg",
      "uploaded_at": "2024-01-15T10:25:00Z",
      "url": "/uploads/selfie_20240115.jpg"
    },
    "document": {
      "file_id": 9,
      "filename": "passport_20240115.jpg",
      "file_path": "uploads/user_1/passport_20240115.jpg",
      "uploaded_at": "2024-01-15T10:24:00Z",
      "url": "/uploads/passport_20240115.jpg"
    }
  }
}
```

## Error Responses

### 403 Forbidden - User Not KYC Verified
```json
{
  "detail": "User is not KYC verified"
}
```

### 404 Not Found - No Approved KYC Request
```json
{
  "detail": "No approved KYC request found"
}
```

### 401 Unauthorized - Invalid/Missing Token
```json
{
  "detail": "Could not validate credentials"
}
```

## Usage in Mobile App

### 1. Request Example (JavaScript/React Native)

```javascript
const getVerifiedKYC = async () => {
  try {
    const response = await fetch('http://YOUR_SERVER:8000/api/v1/kyc/verified-data', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${userToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch KYC data');
    }
    
    const data = await response.json();
    
    // Display user info
    console.log('User:', data.full_name);
    console.log('KYC Status:', data.kyc_details.status);
    
    // Load selfie image
    const selfieUrl = `http://YOUR_SERVER:8000${data.files.selfie.url}`;
    setProfileImage(selfieUrl);
    
    return data;
  } catch (error) {
    console.error('Error fetching KYC data:', error);
  }
};
```

### 2. Display Selfie Image

```jsx
// React Native component
import { Image } from 'react-native';

const ProfileScreen = ({ kycData }) => {
  const serverUrl = 'http://YOUR_SERVER:8000';
  const selfieUrl = kycData?.files?.selfie?.url 
    ? `${serverUrl}${kycData.files.selfie.url}`
    : null;

  return (
    <View>
      {selfieUrl && (
        <Image 
          source={{ uri: selfieUrl }}
          style={{ width: 150, height: 150, borderRadius: 75 }}
        />
      )}
      <Text>{kycData?.full_name}</Text>
      <Text>Status: {kycData?.kyc_details?.status}</Text>
    </View>
  );
};
```

## Image File Access

Images are served via FastAPI's StaticFiles mount point:
- **Mount path:** `/uploads`
- **Physical directory:** `./uploads/`
- **Access pattern:** `GET /uploads/{filename}`

Example:
- File path in database: `uploads/user_1/selfie_20240115.jpg`
- URL to access: `http://YOUR_SERVER:8000/uploads/selfie_20240115.jpg`

## Security Considerations

1. **Authentication Required:** Endpoint requires valid JWT token
2. **User Isolation:** Only returns data for the authenticated user
3. **Verification Check:** Only works for users with `kyc_verified = true`
4. **Latest Data:** Returns the most recent approved KYC request

## Testing

### Using cURL

```bash
curl -X GET "http://localhost:8000/api/v1/kyc/verified-data" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### Using Swagger UI

1. Navigate to `http://localhost:8000/docs`
2. Click on "Authorize" and enter your JWT token
3. Find the `GET /api/v1/kyc/verified-data` endpoint under KYC section
4. Click "Try it out" and "Execute"

## Implementation Details

### File Location
- **Path:** `app/api/v1/kyc.py`
- **Function:** `get_verified_kyc_data()`
- **Lines:** ~220-304

### Dependencies
- Requires `KYCStatus.APPROVED` enum value
- Uses `user_file_crud.get_user_file_by_type()` to fetch files
- Queries `KYCRequest` table with status filter
- Orders by `reviewed_at` descending to get latest approval

### Database Queries
1. Check `current_user.kyc_verified` flag
2. Query `kyc_requests` table for approved status
3. Query `user_files` table for selfie (FileType.KYC_SELFIE)
4. Query `user_files` table for document (FileType.KYC_DOCUMENT)

## Notes

- The endpoint returns `null` for file objects if they don't exist
- Both selfie and document are optional in the response
- The `url` field provides a relative path for direct image access
- Images are publicly accessible once uploaded (consider adding authentication for production)

## Next Steps

1. ✅ Endpoint created and tested for syntax errors
2. ⏳ Test with real data using approved KYC requests
3. ⏳ Integrate into mobile app profile screen
4. ⏳ Add image loading error handling in mobile app
5. ⏳ Consider adding image authentication/authorization for production
