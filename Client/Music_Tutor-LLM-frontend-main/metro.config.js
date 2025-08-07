const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Fix for Metro bundler compatibility
config.resolver.assetExts.push('bin');

// Completely disable file watching to prevent EMFILE errors
config.watchFolders = [];
config.server = {
  enhanceMiddleware: (middleware) => middleware,
};

// Minimal file watching configuration
config.watcher = {
  healthCheck: {
    enabled: false,
  },
  watchman: {
    defer_states: ['hg.update'],
  },
};

// Reduce resolver complexity
config.resolver.platforms = ['web', 'native'];

module.exports = config;