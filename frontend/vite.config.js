import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const proxyTarget = env.VITE_API_PROXY_TARGET || "http://127.0.0.1:24041";

  return {
    plugins: [vue()],
    server: {
      host: true,
      port: 24043,
      proxy: {
        "/api": {
          target: proxyTarget,
          changeOrigin: true
        },
        // 将 /{安全路由码} 转发到后端，便于本地开发时通过前端端口访问后台入口
        "^/[A-Za-z0-9]{6,32}$": {
          target: proxyTarget,
          changeOrigin: true
        }
      }
    }
  };
});
