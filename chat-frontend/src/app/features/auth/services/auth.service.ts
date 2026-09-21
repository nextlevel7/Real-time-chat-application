import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, Observable, tap, throwError } from 'rxjs';
import { AuthResponse, LoginPayload, RegisterPayload, User } from '../models/auth.models';

const TOKEN_KEY = 'access_token';

function getStorage(): Storage | null {
  if (typeof window !== 'undefined' && window.localStorage) {
    return window.localStorage;
  }
  return null;
}

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  readonly currentUser = signal<User | null>(null);
  readonly token = signal<string | null>(this.getStoredToken());
  readonly isAuthenticated = computed(() => !!this.token());
  readonly isLoading = signal<boolean>(false);
  readonly errorMessage = signal<string | null>(null);

  constructor() {
    if (this.token()) {
      this.fetchCurrentUser().subscribe({
        error: () => this.logout(),
      });
    }
  }

  login(payload: LoginPayload): Observable<AuthResponse> {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    return this.http.post<AuthResponse>('/api/auth/login', payload).pipe(
      tap((res) => {
        this.setSession(res.accessToken, res.user);
        this.isLoading.set(false);
      }),
      catchError((err: HttpErrorResponse) => {
        this.isLoading.set(false);
        const msg = err.error?.error?.message || 'Login failed. Please check your credentials.';
        this.errorMessage.set(msg);
        return throwError(() => err);
      }),
    );
  }

  register(payload: RegisterPayload): Observable<{ user: User }> {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    return this.http.post<{ user: User }>('/api/auth/register', payload).pipe(
      tap(() => {
        this.isLoading.set(false);
      }),
      catchError((err: HttpErrorResponse) => {
        this.isLoading.set(false);
        const msg = err.error?.error?.message || 'Registration failed.';
        this.errorMessage.set(msg);
        return throwError(() => err);
      }),
    );
  }

  fetchCurrentUser(): Observable<{ user: User }> {
    return this.http.get<{ user: User }>('/api/auth/me').pipe(
      tap((res) => {
        this.currentUser.set(res.user);
      }),
    );
  }

  logout(): void {
    const storage = getStorage();
    if (storage) {
      storage.removeItem(TOKEN_KEY);
    }
    this.token.set(null);
    this.currentUser.set(null);
    this.router.navigate(['/login']);
  }

  private setSession(token: string, user: User): void {
    const storage = getStorage();
    if (storage) {
      storage.setItem(TOKEN_KEY, token);
    }
    this.token.set(token);
    this.currentUser.set(user);
  }

  private getStoredToken(): string | null {
    const storage = getStorage();
    return storage ? storage.getItem(TOKEN_KEY) : null;
  }
}
