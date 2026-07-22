import { scanBlob } from "./scanner-core.mjs";

let cancelled = false;

self.onmessage = async (event) => {
  const { type } = event.data || {};
  if (type === "cancel") {
    cancelled = true;
    return;
  }
  if (type !== "scan") return;

  cancelled = false;
  const { file, chunkSize } = event.data;
  try {
    const result = await scanBlob(file, {
      chunkSize,
      shouldCancel: () => cancelled,
      onProgress: (payload) => {
        self.postMessage({ type: "progress", payload });
      },
    });
    self.postMessage({ type: "done", payload: result });
  } catch (error) {
    self.postMessage({
      type: "error",
      error: error instanceof Error ? error.message : String(error),
    });
  }
};
