# Mobile App Integration - Quick Reference

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies

**React Native + Expo:**
```bash
npx expo install expo-notifications expo-device
```

**React Native + Firebase:**
```bash
npm install @react-native-firebase/app @react-native-firebase/messaging
```

### Step 2: Request Permissions & Get Token

**Expo:**
```javascript
import * as Notifications from 'expo-notifications';

// Call this when user logs in
async function setupPushNotifications() {
  const { status } = await Notifications.requestPermissionsAsync();
  
  if (status === 'granted') {
    const token = (await Notifications.getExpoPushTokenAsync()).data;
    await registerTokenWithBackend(token);
  }
}
```

**Firebase:**
```javascript
import messaging from '@react-native-firebase/messaging';

// Call this when user logs in
async function setupPushNotifications() {
  await messaging().requestPermission();
  const token = await messaging().getToken();
  await registerTokenWithBackend(token);
}
```

### Step 3: Send Token to Backend

```javascript
async function registerTokenWithBackend(deviceToken) {
  const response = await fetch('YOUR_API_URL/api/v1/users/fcm-token', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${yourAccessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ 
      fcm_device_token: deviceToken 
    })
  });
  
  if (response.ok) {
    console.log('✓ Push notifications enabled');
  }
}
```

### Step 4: Handle Incoming Notifications

**Expo:**
```javascript
import * as Notifications from 'expo-notifications';
import { useNavigation } from '@react-navigation/native';

// Configure notification handler
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

// Handle notification tap
function App() {
  const navigation = useNavigation();
  
  useEffect(() => {
    // Notification tapped while app is open
    const subscription = Notifications.addNotificationResponseReceivedListener(
      response => {
        const data = response.notification.request.content.data;
        
        if (data.type === 'transaction' && data.transaction_id) {
          // Navigate to transaction details
          navigation.navigate('TransactionDetails', {
            id: data.transaction_id
          });
        }
      }
    );
    
    return () => subscription.remove();
  }, []);
  
  return <YourAppComponents />;
}
```

**Firebase:**
```javascript
import messaging from '@react-native-firebase/messaging';
import { useNavigation } from '@react-navigation/native';

function App() {
  const navigation = useNavigation();
  
  useEffect(() => {
    // Foreground notifications
    const unsubscribe = messaging().onMessage(async remoteMessage => {
      console.log('Notification received:', remoteMessage);
      // Show in-app notification or update badge
    });
    
    // Background/quit state - notification tapped
    messaging().onNotificationOpenedApp(remoteMessage => {
      const data = remoteMessage.data;
      
      if (data.type === 'transaction' && data.transaction_id) {
        navigation.navigate('TransactionDetails', {
          id: data.transaction_id
        });
      }
    });
    
    // App opened from quit state via notification
    messaging()
      .getInitialNotification()
      .then(remoteMessage => {
        if (remoteMessage) {
          const data = remoteMessage.data;
          
          if (data.type === 'transaction' && data.transaction_id) {
            navigation.navigate('TransactionDetails', {
              id: data.transaction_id
            });
          }
        }
      });
    
    return unsubscribe;
  }, []);
  
  return <YourAppComponents />;
}
```

### Step 5: Handle Logout

```javascript
async function logout() {
  // Remove FCM token from backend
  await fetch('YOUR_API_URL/api/v1/users/fcm-token', {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${yourAccessToken}`
    }
  });
  
  // Clear local auth
  await AsyncStorage.removeItem('access_token');
  
  // Navigate to login
  navigation.navigate('Login');
}
```

---

## 📱 Complete Example

```javascript
// PushNotificationService.js
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = 'https://your-api.com';

// Configure notification appearance
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export class PushNotificationService {
  static async setup() {
    if (!Device.isDevice) {
      console.log('Push notifications only work on physical devices');
      return null;
    }
    
    // Request permissions
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    
    if (finalStatus !== 'granted') {
      console.log('Permission denied for push notifications');
      return null;
    }
    
    // Get token
    const token = (await Notifications.getExpoPushTokenAsync()).data;
    
    // Register with backend
    await this.registerToken(token);
    
    return token;
  }
  
  static async registerToken(deviceToken) {
    try {
      const accessToken = await AsyncStorage.getItem('access_token');
      
      const response = await fetch(`${API_URL}/api/v1/users/fcm-token`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ fcm_device_token: deviceToken })
      });
      
      if (response.ok) {
        console.log('✓ FCM token registered');
        await AsyncStorage.setItem('fcm_token', deviceToken);
      } else {
        console.error('✗ Failed to register FCM token');
      }
    } catch (error) {
      console.error('Error registering FCM token:', error);
    }
  }
  
  static async removeToken() {
    try {
      const accessToken = await AsyncStorage.getItem('access_token');
      
      await fetch(`${API_URL}/api/v1/users/fcm-token`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      
      await AsyncStorage.removeItem('fcm_token');
      console.log('✓ FCM token removed');
    } catch (error) {
      console.error('Error removing FCM token:', error);
    }
  }
  
  static setupNotificationListener(navigation) {
    // Handle notification tap
    const subscription = Notifications.addNotificationResponseReceivedListener(
      response => {
        const data = response.notification.request.content.data;
        
        // Handle different notification types
        if (data.type === 'transaction') {
          if (data.transaction_id) {
            navigation.navigate('TransactionDetails', {
              id: parseInt(data.transaction_id)
            });
          } else {
            navigation.navigate('Transactions');
          }
        }
      }
    );
    
    return subscription;
  }
}

// App.js
import { PushNotificationService } from './services/PushNotificationService';
import { useEffect, useRef } from 'react';
import { useNavigation } from '@react-navigation/native';

export default function App() {
  const navigation = useNavigation();
  const notificationListener = useRef();
  
  useEffect(() => {
    // Setup push notifications on app start
    PushNotificationService.setup();
    
    // Setup notification tap handler
    notificationListener.current = 
      PushNotificationService.setupNotificationListener(navigation);
    
    return () => {
      if (notificationListener.current) {
        notificationListener.current.remove();
      }
    };
  }, []);
  
  return (
    <NavigationContainer>
      {/* Your app screens */}
    </NavigationContainer>
  );
}

// AuthContext.js or Login screen
import { PushNotificationService } from './services/PushNotificationService';

// After successful login
async function handleLogin(credentials) {
  const response = await loginAPI(credentials);
  
  if (response.success) {
    await AsyncStorage.setItem('access_token', response.access_token);
    
    // Setup push notifications
    await PushNotificationService.setup();
    
    navigation.navigate('Home');
  }
}

// On logout
async function handleLogout() {
  // Remove FCM token
  await PushNotificationService.removeToken();
  
  // Clear auth
  await AsyncStorage.removeItem('access_token');
  
  navigation.navigate('Login');
}
```

---

## 🎯 Notification Data Structure

When you receive a notification, it contains:

```javascript
{
  notification: {
    title: "Payment Received",
    body: "You received 8,275.50 INR from abhi@dari"
  },
  data: {
    type: "transaction",
    notification_type: "received",  // 'sent', 'received', 'confirmed', 'failed'
    amount: "8275.50",
    currency: "INR",
    from_to: "abhi@dari",
    transaction_id: "123"
  }
}
```

Handle it like:
```javascript
const handleNotification = (data) => {
  switch (data.notification_type) {
    case 'sent':
      // Navigate to sent transaction
      navigation.navigate('TransactionDetails', { id: data.transaction_id });
      break;
    case 'received':
      // Navigate to received transaction, maybe show celebration
      navigation.navigate('TransactionDetails', { id: data.transaction_id });
      showSuccessAnimation();
      break;
    case 'confirmed':
      // Update transaction status in UI
      updateTransactionStatus(data.transaction_id, 'confirmed');
      break;
    case 'failed':
      // Show error message
      showAlert('Transaction Failed', 'Your transaction could not be completed');
      break;
  }
};
```

---

## 🐛 Troubleshooting

### "Permission denied"
```javascript
// Check permission status
const { status } = await Notifications.getPermissionsAsync();
console.log('Permission status:', status);

// If denied, ask user to enable in settings
if (status === 'denied') {
  Alert.alert(
    'Enable Notifications',
    'Please enable notifications in your device settings to receive payment alerts',
    [{ text: 'Open Settings', onPress: () => Linking.openSettings() }]
  );
}
```

### "Token not registering"
```javascript
// Add error handling
try {
  const token = await Notifications.getExpoPushTokenAsync();
  console.log('FCM Token:', token);
  
  const response = await registerTokenWithBackend(token.data);
  console.log('Registration response:', response);
} catch (error) {
  console.error('FCM Error:', error);
}
```

### "Notifications not appearing"
```javascript
// Test with a local notification
await Notifications.scheduleNotificationAsync({
  content: {
    title: "Test Notification",
    body: "If you see this, notifications are working!",
  },
  trigger: null, // Show immediately
});
```

---

## 📋 Checklist

- [ ] Dependencies installed
- [ ] Permissions requested on login
- [ ] FCM token sent to backend
- [ ] Notification handler configured
- [ ] Deep linking to transaction details working
- [ ] Token removed on logout
- [ ] Tested on physical device
- [ ] Error handling added

---

## 🔗 API Endpoints Reference

```
POST   /api/v1/users/fcm-token
Body:  { "fcm_device_token": "string" }
Auth:  Bearer token required

DELETE /api/v1/users/fcm-token
Auth:  Bearer token required
```

---

## 📚 Resources

- Expo Notifications: https://docs.expo.dev/push-notifications/
- Firebase Messaging: https://rnfirebase.io/messaging/usage
- Deep Linking: https://reactnavigation.org/docs/deep-linking

---

**Quick Questions?**
- Not receiving notifications? Check backend logs
- Token not saving? Verify auth token is valid
- Deep linking not working? Check navigation structure
