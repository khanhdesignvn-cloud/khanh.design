(function () {
  "use strict";
  const DB_NAME = "horus-showcase";
  const STORE = "images";
  function database() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, 1);
      request.onupgradeneeded = () =>
        request.result.createObjectStore(STORE, { keyPath: "id" });
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
  async function transact(mode, operation) {
    const db = await database();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(STORE, mode);
      const request = operation(transaction.objectStore(STORE));
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
      transaction.oncomplete = () => db.close();
    });
  }
  window.HorusDB = {
    put: (record) => transact("readwrite", (store) => store.put(record)),
    list: (projectId) =>
      transact("readonly", (store) => store.getAll()).then((rows) =>
        rows.filter((row) => row.projectId === projectId),
      ),
    clear: () => transact("readwrite", (store) => store.clear()),
  };
})();
