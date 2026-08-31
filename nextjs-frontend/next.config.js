const path = require('path');

const workspaceRoot = path.join(__dirname, '..');

/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    root: workspaceRoot,
  },
  outputFileTracingRoot: workspaceRoot,
};

module.exports = nextConfig;
