module.exports = function(config) {
  config.set({
    basePath: '',
    frameworks: ['jasmine'],
    files: ['src/**/*.spec.js'],
    preprocessors: { 'src/**/*.spec.js': ['webpack'] },
    webpack: {
      mode: 'development',
      module: {
        rules: [
          { test: /\.html$/, use: 'html-loader' },
          { test: /\.css$/, use: ['style-loader', 'css-loader'] },
        ],
      },
      plugins: [
        require('webpack').DefinePlugin
          ? new (require('webpack').DefinePlugin)({
              'process.env.API_BASE_URL': JSON.stringify('http://localhost:8080/web/api/v1'),
            })
          : null,
      ].filter(Boolean),
    },
    reporters: ['progress'],
    browsers: ['ChromiumHeadless'],
    customLaunchers: {
      ChromiumHeadless: {
        base: 'Chromium',
        flags: ['--headless', '--no-sandbox', '--disable-gpu',
                '--disable-dev-shm-usage', '--remote-debugging-port=9222'],
      },
    },
    singleRun: false,
    concurrency: Infinity,
  });
};
