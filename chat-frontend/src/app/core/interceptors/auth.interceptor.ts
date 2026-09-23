import { HttpInterceptorFn } from '@angular/common/http';
import { TOKEN_KEY } from '../../features/auth/services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token =
    typeof window !== 'undefined' && window.localStorage
      ? window.localStorage.getItem(TOKEN_KEY)
      : null;

  if (token && req.url.startsWith('/api')) {
    const authReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
      },
    });
    return next(authReq);
  }

  return next(req);
};
