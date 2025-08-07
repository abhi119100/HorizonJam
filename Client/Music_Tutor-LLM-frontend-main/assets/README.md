# Assets Directory

This directory contains all static assets for the HorizonJam Music Tutor app.

## Required Assets

### Images
Place the following images in the `assets/` directory:

- `icon.png` - App icon (1024x1024px)
- `splash.png` - Splash screen image (1284x2778px for iPhone 12 Pro Max)
- `adaptive-icon.png` - Android adaptive icon foreground (1024x1024px)
- `favicon.png` - Web favicon (32x32px)

### Audio (Optional)
Place any demo audio files in the `assets/audio/` directory:

- Sample chord progressions for testing
- Demo recordings for new users
- Audio feedback sounds

## Asset Guidelines

### App Icon (`icon.png`)
- Size: 1024x1024 pixels
- Format: PNG with transparency
- Design: Should represent music/audio theme
- Colors: Use app's primary color scheme

### Splash Screen (`splash.png`)
- Size: 1284x2778 pixels (iPhone 12 Pro Max resolution)
- Format: PNG
- Design: Simple, clean design with app logo
- Background: Use app's background color

### Adaptive Icon (`adaptive-icon.png`)
- Size: 1024x1024 pixels
- Format: PNG with transparency
- Design: Foreground element for Android adaptive icons
- Safe area: Keep important elements within 66% of canvas

### Favicon (`favicon.png`)
- Size: 32x32 pixels
- Format: PNG
- Design: Simplified version of app icon

## Creating Assets

You can create these assets using:
- Design tools: Figma, Sketch, Adobe Illustrator
- Online generators: Favicon.io, App Icon Generator
- AI tools: Midjourney, DALL-E for design inspiration

## Expo Asset Optimization

Expo automatically optimizes assets during build:
- Images are compressed for different screen densities
- Multiple resolutions are generated automatically
- Assets are bundled efficiently for each platform

For more information, see: https://docs.expo.dev/guides/assets/