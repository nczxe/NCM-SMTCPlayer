(function () {
    const TOKEN_KEY = 'smtc_auth_token';
    const nativeFetch = window.fetch.bind(window);

    window.smtcAuth = {
        getToken() {
            return localStorage.getItem(TOKEN_KEY) || '';
        },
        setToken(token) {
            localStorage.setItem(TOKEN_KEY, token);
        },
        clearToken() {
            localStorage.removeItem(TOKEN_KEY);
        }
    };

    window.fetch = function (resource, options = {}) {
        const url = typeof resource === 'string' ? resource : resource.url;
        const isApi = url && url.startsWith('/api/');
        const isAuth = url && url.startsWith('/api/auth/');
        if (isApi && !isAuth) {
            options.headers = new Headers(options.headers || {});
            const token = window.smtcAuth.getToken();
            if (token) {
                options.headers.set('X-SMTC-Token', token);
            }
        }
        return nativeFetch(resource, options);
    };

    window.smtcNativeFetch = nativeFetch;
})();
