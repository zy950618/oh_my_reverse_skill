(function (root) {
  function stableStringify(value) {
    if (value === null || typeof value !== 'object') return JSON.stringify(value);
    if (Array.isArray(value)) return '[' + value.map(stableStringify).join(',') + ']';
    return '{' + Object.keys(value).sort().map(function (key) {
      return JSON.stringify(key) + ':' + stableStringify(value[key]);
    }).join(',') + '}';
  }
  function fnv1a(input) {
    var hash = 2166136261;
    for (var i = 0; i < input.length; i++) {
      hash ^= input.charCodeAt(i);
      hash = Math.imul(hash, 16777619) >>> 0;
    }
    return ('00000000' + hash.toString(16)).slice(-8);
  }
  function collectEnv() {
    var nav = root.navigator || {};
    var loc = root.location || { href: 'page-runtime://local' };
    return {
      userAgent: nav.userAgent || 'node-v8',
      platform: nav.platform || 'node',
      language: nav.language || (nav.languages && nav.languages[0]) || 'en-US',
      href: loc.href || 'page-runtime://local'
    };
  }
  function signPayload(payload) {
    var env = collectEnv();
    var normalized = stableStringify(payload);
    var signatureBase = normalized + '|action=' + payload.action + '|item=' + payload.item_id;
    return {
      algorithm: 'fnv1a-demo-signature',
      input_hash: fnv1a(normalized),
      signature: fnv1a(signatureBase),
      env_hash: fnv1a(stableStringify(env)),
      dependencies: ['navigator.userAgent', 'navigator.platform', 'navigator.language', 'location.href'],
      output: normalized
    };
  }
  root.__REALISTIC_LAB__ = { stableStringify: stableStringify, fnv1a: fnv1a, collectEnv: collectEnv, signPayload: signPayload };
})(typeof globalThis !== 'undefined' ? globalThis : this);
