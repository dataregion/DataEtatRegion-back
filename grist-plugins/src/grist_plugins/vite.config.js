import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  root: './',
  base: '/',
  build: {
    outDir: 'static/dist',
    emptyOutDir: true,
    minify: 'terser',
    sourcemap: false,
    rollupOptions: {
      input: {
        'to-superset': resolve(__dirname, 'static/js/to-superset.js'),
      },
      output: {
        entryFileNames: 'js/[name].min.js',
        chunkFileNames: 'js/[name].chunk.min.js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.names.split('.');
          const ext = info[info.length - 1];
          if (/png|jpe?g|gif|svg|webp|woff2?|ttf|otf|eot/.test(ext)) {
            return `assets/[name]-[hash][extname]`;
          } else if (ext === 'css') {
            return `css/[name]-[hash][extname]`;
          }
          return `[name]-[hash][extname]`;
        }
      }
    }
  },
  server: {
    port: 5173,
    host: 'localhost',
    hmr: {
      protocol: 'ws',
      host: 'localhost',
      port: 5173
    }
  }
});
