const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const webpack = require('webpack');
require('dotenv').config();

module.exports = {
  entry: './src/index.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.[contenthash].js',
    clean: true,
  },
  module: {
    rules: [
      { test: /\.css$/, use: ['style-loader', 'css-loader'] },
      {
        test: /\.html$/,
        use: 'html-loader',
        exclude: path.resolve(__dirname, 'src/index.html'),
      },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({ template: './src/index.html' }),
    new webpack.DefinePlugin({
      'process.env.API_BASE_URL': JSON.stringify(
        process.env.API_BASE_URL || 'http://localhost:8080/web/api/v1'
      ),
    }),
  ],
  devServer: {
    port: 4200,
    historyApiFallback: true,
    proxy: [{ context: ['/api'], target: 'http://localhost:8080' }],
  },
};
