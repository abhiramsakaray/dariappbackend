# Expo Push Notifications - Mobile App Integration Guide

## 🎉 **AUTO-REGISTRATION ON LOGIN IS NOW ENABLED!**

Your backend now automatically registers push notification tokens during login! Simply include the token in your login request.

---

## 📱 Complete Mobile App Setup

### Step 1: Install Dependencies

```bash
npx expo install expo-notifications expo-device expo-constants
```

### Step 2: Create API Service

Create `src/api/services/pushNotificationService.js`:

```javascript
import api from '../api';
import { API_ENDPOINTS } from '../../constants';

export const pushNotificationService = {
  /**
   * Register push notification token with backend
   * NOTE: Auto-registration happens on login, but you can still use this for manual registration
   */
  async registerToken(tokenData) {
    try {
      const response = await api.post('/push/register', tokenData);
      return response.data;
    } catch (error) {
      console.error('Error registering push token:', error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Unregister push notification token
   */
  async unregisterToken(tokenData) {
    try {
      const response = await api.delete('/push/unregister', { data: tokenData });
      return response.data;
    } catch (error) {
      console.error('Error unregistering push token:', error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Get all registered push tokens for current user
   */
  async getTokens(activeOnly = true) {
    try {
      const response = await api.get('/push/tokens', {
        params: { active_only: activeOnly }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching push tokens:', error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Delete a specific push token by ID
   */
  async deleteToken(tokenId) {
    try {
      const response = await api.delete(`/push/tokens/${tokenId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting push token:', error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Send a test notification to all user's devices
   */
  async sendTestNotification() {
    try {
      const response = await api.post('/push/test');
      return response.data;
    } catch (error) {
      console.error('Error sending test notification:', error.response?.data || error.message);
      throw error;
    }
  }
};
```

### Step 3: Create Notification Helper

Create `src/utils/pushNotifications.js`:

```javascript
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Configure how notifications are handled when app is in foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

/**
 * Request notification permissions and get Expo Push Token
 * @returns {Promise<string|null>} Expo push token or null if failed
 */
export async function registerForPushNotifications() {
  let token;

  // Must use physical device for Push Notifications
  if (!Device.isDevice) {
    console.warn('Must use physical device for Push Notifications');
    return null;
  }

  try {
    // Check/request permissions
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    
    if (finalStatus !== 'granted') {
      console.warn('Permission not granted for push notifications');
      return null;
    }
    
    // Get Expo push token
    token = (await Notifications.getExpoPushTokenAsync({
      projectId: Constants.expoConfig?.extra?.eas?.projectId,
    })).data;
    
    console.log('✓ Expo Push Token obtained:', token);
    
    // Android: Set up notification channel
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'default',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#4CAF50',
      });
      
      // Create channels for different notification types
      await Notifications.setNotificationChannelAsync('payments', {
        name: 'Payments',
        importance: Notifications.AndroidImportance.HIGH,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#4CAF50',
      });
      
      await Notifications.setNotificationChannelAsync('security', {
        name: 'Security',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 500, 500, 500],
        lightColor: '#FF5722',
      });
      
      await Notifications.setNotificationChannelAsync('transactions', {
        name: 'Transactions',
        importance: Notifications.AndroidImportance.HIGH,
        vibrationPattern: [0, 250],
        lightColor: '#2196F3',
      });
    }
    
    return token;
  } catch (error) {
    console.error('Error getting push token:', error);
    return null;
  }
}

/**
 * Set up notification listeners
 * @param {Function} onNotificationReceived - Called when notification received
 * @param {Function} onNotificationTapped - Called when notification tapped
 * @returns {Object} Object with cleanup function
 */
export function setupNotificationListeners(onNotificationReceived, onNotificationTapped) {
  // Listen for notifications received while app is in foreground
  const notificationListener = Notifications.addNotificationReceivedListener(notification => {
    console.log('Notification received:', notification);
    if (onNotificationReceived) {
      onNotificationReceived(notification);
    }
  });

  // Listen for user tapping on notification
  const responseListener = Notifications.addNotificationResponseReceivedListener(response => {
    console.log('Notification tapped:', response);
    const data = response.notification.request.content.data;
    
    if (onNotificationTapped) {
      onNotificationTapped(data);
    }
  });

  // Return cleanup function
  return () => {
    Notifications.removeNotificationSubscription(notificationListener);
    Notifications.removeNotificationSubscription(responseListener);
  };
}

/**
 * Get badge count
 * @returns {Promise<number>}
 */
export async function getBadgeCount() {
  return await Notifications.getBadgeCountAsync();
}

/**
 * Set badge count
 * @param {number} count
 */
export async function setBadgeCount(count) {
  await Notifications.setBadgeCountAsync(count);
}

/**
 * Clear all notifications
 */
export async function clearAllNotifications() {
  await Notifications.dismissAllNotificationsAsync();
}
```

### Step 4: Update Login Flow (AUTO-REGISTRATION) ⭐ **NEW**

The backend now supports **automatic push token registration during login**! Simply include the push token in your OTP verification request:

#### Option A: Auto-Register on Login (Recommended)

Update your `loginWithOTP` function in `src/api/services/authService.js`:

```javascript
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import { registerForPushNotifications } from '../../utils/pushNotifications';

export async function loginWithOTP(email, otp) {
  try {
    // Get push token (silently, doesn't block login if fails)
    let pushTokenData = {};
    try {
      const token = await registerForPushNotifications();
      if (token) {
        pushTokenData = {
          expo_push_token: token,
          device_type: Platform.OS,
          device_name: Device.modelName || `${Platform.OS} Device`,
        };
      }
    } catch (error) {
      console.warn('Could not get push token:', error);
      // Continue with login anyway
    }

    // Login with OTP + push token
    const response = await api.post('/auth/login/verify-otp', {
      email,
      otp,
      ...pushTokenData  // Include push token if available
    });

    return response.data;
  } catch (error) {
    throw error;
  }
}
```

**Benefits:**
- ✅ Automatic registration on every login
- ✅ No separate registration API call needed
- ✅ Always keeps token up-to-date
- ✅ Won't fail login if push token unavailable
- ✅ Multi-device support (each device auto-registers)

#### Option B: Manual Registration After Login

Or continue using manual registration after login (Step 5 below).

---

### Step 5: Integrate in App.js (Manual Registration)

Update your `App.js` or main app component:

```javascript
import React, { useEffect, useRef, useState } from 'react';
import { useNavigation } from '@react-navigation/native';
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import * as Device from 'expo-device';

import { 
  registerForPushNotifications, 
  setupNotificationListeners,
  setBadgeCount
} from './utils/pushNotifications';
import { pushNotificationService } from './api/services/pushNotificationService';
import { useAuth } from './contexts/AuthContext';

export default function App() {
  const navigation = useNavigation();
  const { user, isAuthenticated } = useAuth();
  const [expoPushToken, setExpoPushToken] = useState('');

  // ⚠️ NOTE: If using auto-registration on login (Option A), this is OPTIONAL
  // Register push notifications when user logs in
  useEffect(() => {
    if (isAuthenticated && user) {
      registerAndStorePushToken();
    }
  }, [isAuthenticated, user]);

  // Set up notification listeners
  useEffect(() => {
    const cleanup = setupNotificationListeners(
      handleNotificationReceived,
      handleNotificationTapped
    );

    return cleanup;
  }, []);

  /**
   * Register for push notifications and save token to backend
   */
  const registerAndStorePushToken = async () => {
    try {
      const token = await registerForPushNotifications();
      
      if (token) {
        setExpoPushToken(token);
        
        // Register with backend
        await pushNotificationService.registerToken({
          expo_push_token: token,
          device_type: Platform.OS,
          device_name: Device.modelName || `${Platform.OS} Device`,
        });
        
        console.log('✓ Push token registered with backend');
      }
    } catch (error) {
      console.error('Failed to register push token:', error);
    }
  };

  /**
   * Handle notification received while app is in foreground
   */
  const handleNotificationReceived = (notification) => {
    console.log('Notification received in foreground:', notification);
    
    // Update badge count
    const badge = notification.request.content.badge;
    if (badge !== undefined) {
      setBadgeCount(badge);
    }
    
    // You can show a custom in-app notification here
    // or update your app's state
  };

  /**
   * Handle notification tap
   */
  const handleNotificationTapped = (data) => {
    console.log('Notification tapped with data:', data);
    
    // Navigate based on notification type
    switch (data.type) {
      case 'payment_received':
        navigation.navigate('TransactionDetails', { 
          transactionId: data.transaction_id 
        });
        break;
        
      case 'transaction':
        navigation.navigate('TransactionDetails', { 
          transactionId: data.transaction_id 
        });
        break;
        
      case 'kyc_approved':
      case 'kyc_rejected':
        navigation.navigate('KYCStatus');
        break;
        
      case 'deposit_complete':
        navigation.navigate('DepositDetails', {
          depositId: data.deposit_id
        });
        break;
        
      default:
        navigation.navigate('Notifications');
    }
    
    // Clear badge
    setBadgeCount(0);
  };

  return (
    // ... your app JSX
  );
}
```

### Step 6: Handle Logout

Update your logout function:

```javascript
import { pushNotificationService } from '../api/services/pushNotificationService';
import * as Notifications from 'expo-notifications';

export async function logout() {
  try {
    // Get current token
    const token = await Notifications.getExpoPushTokenAsync();
    
    // Unregister from backend
    if (token?.data) {
      await pushNotificationService.unregisterToken({
        expo_push_token: token.data,
      });
      console.log('✓ Push token unregistered');
    }
  } catch (error) {
    console.error('Failed to unregister push token:', error);
  }
  
  // Continue with logout...
  await AsyncStorage.removeItem('token');
  // etc...
}
```

### Step 6: Add to constants

Update `src/constants/index.js`:

```javascript
export const API_ENDPOINTS = {
  // ... existing endpoints ...
  
  // Push Notifications
  PUSH_REGISTER: '/push/register',
  PUSH_UNREGISTER: '/push/unregister',
  PUSH_TOKENS: '/push/tokens',
  PUSH_TEST: '/push/test',
};
```

### Step 7: Add Permissions to app.json

Update your `app.json`:

```json
{
  "expo": {
    "name": "DARI Wallet",
    "plugins": [
      [
        "expo-notifications",
        {
          "icon": "./assets/notification-icon.png",
          "color": "#ffffff",
          "sounds": ["./assets/notification-sound.wav"]
        }
      ]
    ],
    "notification": {
      "icon": "./assets/notification-icon.png",
      "color": "#4CAF50",
      "androidMode": "default",
      "androidCollapsedTitle": "DARI Wallet"
    },
    "android": {
      "permissions": [
        "RECEIVE_BOOT_COMPLETED",
        "VIBRATE",
        "com.google.android.c2dm.permission.RECEIVE"
      ]
    },
    "ios": {
      "infoPlist": {
        "UIBackgroundModes": ["remote-notification"]
      }
    }
  }
}
```

---

## 🧪 Testing

### Test on Physical Device:

1. **Install app on device**
2. **Login to app**
3. **Grant notification permissions**
4. **Check console for**: "✓ Push token registered with backend"
5. **Send test from backend**:
   ```bash
   curl -X POST http://YOUR_IP:8000/api/v1/push/test \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```
6. **Verify notification received on device**

### Test Different States:

- **App in foreground**: Notification appears in notification area
- **App in background**: Notification appears, tap opens app
- **App closed**: Notification appears, tap opens app
- **Device locked**: Notification appears on lock screen

---

## 🎯 Notification Types

### Payment Received
```javascript
{
  title: "Payment Received 💰",
  body: "You received $50 from john@dari",
  data: {
    type: "payment_received",
    amount: "50",
    sender: "john@dari",
    transaction_id: "tx_123"
  }
}
```

### Transaction Complete
```javascript
{
  title: "Transaction Complete",
  body: "Your transaction of $100 was successful",
  data: {
    type: "transaction",
    transaction_id: "tx_456",
    status: "complete"
  }
}
```

### KYC Status
```javascript
{
  title: "KYC Approved ✓",
  body: "Your identity verification has been approved!",
  data: {
    type: "kyc_approved"
  }
}
```

---

## 🔧 Troubleshooting

**Issue:** "Must use physical device"
- **Solution:** Push notifications only work on physical devices, not simulators

**Issue:** Token registration fails
- **Solution:** Check backend is running, check auth token is valid

**Issue:** Notifications not received
- **Solution:** 
  - Check device has internet connection
  - Verify permissions granted
  - Check token is registered and active
  - Test with `/push/test` endpoint

**Issue:** Badge count not updating
- **Solution:** Call `setBadgeCount()` manually when handling notifications

---

## ✅ Checklist

### Backend Setup (✅ COMPLETED!)
- [x] Push tokens table created
- [x] Auto-registration on login enabled
- [x] Transaction notifications integrated
- [x] KYC notifications integrated
- [x] Notification helper functions ready

### Mobile App Setup
- [ ] Install expo-notifications
- [ ] Create API service
- [ ] Create notification helper
- [ ] **Update login flow with auto-registration (RECOMMENDED)**
- [ ] Integrate notification listeners in App.js
- [ ] Handle logout (unregister token)
- [ ] Update app.json with projectId
- [ ] Test on physical device
- [ ] Verify all notification types
- [ ] Test foreground/background/closed states

---

## 📊 What's Working Now

### ✅ Automatic Features (No Mobile Changes Needed Yet)

1. **Auto-Registration on Login**: Backend accepts push token during OTP verification
2. **Transaction Notifications**: Automatic Expo push notifications sent after every successful transaction
3. **KYC Notifications**: Automatic Expo push notifications on approval/rejection
4. **Multi-Device Support**: Each device auto-registers separately
5. **Error Handling**: Invalid tokens automatically deactivated

### 🔧 What Mobile App Needs To Do

1. **Get push token** from Expo
2. **Include token in login** request (recommended) OR register manually after login
3. **Listen for notifications** (foreground, background, tap events)
4. **Handle navigation** based on notification data
5. **Unregister on logout**

---

## 🎉 Summary

Your backend is **fully ready** for Expo push notifications! 

- ✅ Database table created
- ✅ Auto-registration works on login
- ✅ Notifications send automatically for:
  - Payment received
  - Payment sent
  - KYC approved/rejected
  - (Deposit/withdrawal helpers ready when those features are implemented)

Just integrate the mobile app code and you're good to go! 🚀

---

**Ready to receive notifications! 🔔**
