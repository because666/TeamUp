/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly MODE: "fixture" | string;
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_API_TRANSPORT?: "http" | "cloudbase" | string;
  readonly VITE_CLOUDBASE_ENV_ID?: string;
  readonly VITE_CLOUDBASE_SERVICE?: string;
  readonly VITE_CLOUDBASE_API_PREFIX?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module '*.vue' {
  import { DefineComponent } from 'vue'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/ban-types
  const component: DefineComponent<{}, {}, any>
  export default component
}
