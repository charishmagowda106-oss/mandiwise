module.exports = {
  root: true,
  env: { browser: true, es2021: true },
  extends: ['eslint:recommended'],
  plugins: ['react'],
  ignorePatterns: ['dist'],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: { jsx: true },
  },
  rules: {
    'react/jsx-uses-react': 'error',
    'react/jsx-uses-vars': 'error',
  },
};
