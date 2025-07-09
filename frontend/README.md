# MapApp - React Native Map Application

A cross-platform mobile frontend application built with React Native, Expo, and TypeScript.

## 🚀 Quick Start

### Prerequisites
- Node.js (v18 or later)
- npm or yarn
- Expo CLI (`npm install -g @expo/cli`)
- iOS Simulator (Mac), Android Studio/Emulator or ExpoGo app

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Setup environment variables**
   ```bash
   cp .app.template.json .app.json
   ```
   Edit `.app.json` and add your Google Maps API keys

   > **_NOTE:_**  API Keys used in production will be directly linked to the apps build. Currently I am just using unrestricted keys in development.

4. **Start the development server**
   ```bash
   npx expo start
   ```

5. **Run on device/simulator**
   - iOS: Press `i` or scan QR code with Expo Go
   - Android: Press `a` or scan QR code with Expo Go

## 🛠️ Technology Stack

- **React Native**: Cross-platform mobile development
- **Expo**: Development platform and build service
- **TypeScript**: Static type checking
- **react-native-maps**: Map component library
- **expo-location**: Location and permissions handling

## 📁 Project Structure

```
TODO
```

## 🔧 Development

### Available Scripts

```bash
# Start development server
npm start

# Start with cache cleared
npm run start:clear

# Run on iOS simulator
npm run ios

# Run on Android emulator
npm run android

# Run type checking
npm run type-check

# Build for production
npm run build
```

### Debug Commands

```bash
# Clear Expo cache
npx expo start --clear

# Reset Metro bundler
npx expo start --reset-cache

# Check package versions
npm ls react-native-maps expo-location

# View device logs
npx expo logs --type=device
```

## 🚢 Deployment

### Development Build
```bash
# Create development build
npx expo build:ios
npx expo build:android
```

### Production Build with EAS
```bash
# Install EAS CLI
npm install -g @expo/eas-cli

# Configure EAS
eas build:configure

# Build for production
eas build --platform all
```

## 📚 Additional Resources

- [React Native Documentation](https://reactnative.dev/docs/getting-started)
- [Expo Documentation](https://docs.expo.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)
- [Google Maps Platform](https://developers.google.com/maps)
- [React Native Maps GitHub](https://github.com/react-native-maps/react-native-maps)