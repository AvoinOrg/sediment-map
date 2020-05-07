const path = require('path');
const ThreadsPlugin = require('threads-plugin')

const isProduction = (process.env.NODE_ENV === 'production');

module.exports = {
  entry: ['babel-polyfill', './src/index.jsx'],

  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'app.bundle.js',
    globalObject: 'this',
  },

  plugins: [
    new ThreadsPlugin(),
  ],

  module: {
    rules: [
//        test: /\.worker\.js$/,
//        use: [{
//          loader: 'babel-loader',
//          // options are in .babelrc
//        }, {
//          loader: 'worker-loader',
//          options: {
//            inline: true,
//          },
//       }],
      {
        test: /\.worker\.js$/,
        use: {
          loader: 'worker-loader',
          options: {
            name: isProduction ? '[hash].worker.min.js' : '[hash].worker.js',
            inline: true,
            fallback: true,
          },
        },
      }, {
        test: /\.jsx?$/,
        exclude: /(node_modules|bower_components)/,
        use: {
          loader: 'babel-loader',
          // options are in .babelrc
        },
      }, {
        test: /\.css$/,
        use: [
          { loader: 'style-loader' },
          { loader: 'css-loader' },
        ],
      },
    ],
  },

  resolve: {
    extensions: ['.js', '.jsx'],
    alias: { 'react-dom': '@hot-loader/react-dom'  },
  },

  node: {
    fs: 'empty',
  },

  devServer: {
    host: '0.0.0.0',
    port: 8091,
    inline: true,
    disableHostCheck: true,
    watchContentBase: true,
    overlay: {
      warnings: true,
      errors: true,
    },
  },

  devtool: 'source-map',
  cache: true,
};
