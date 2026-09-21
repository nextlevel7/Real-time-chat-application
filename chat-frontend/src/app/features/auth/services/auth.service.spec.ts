import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { AuthService } from './auth.service';

class MockStorage implements Storage {
  private store: Record<string, string> = {};
  get length(): number {
    return Object.keys(this.store).length;
  }
  clear(): void {
    this.store = {};
  }
  getItem(key: string): string | null {
    return this.store[key] ?? null;
  }
  key(index: number): string | null {
    return Object.keys(this.store)[index] ?? null;
  }
  removeItem(key: string): void {
    delete this.store[key];
  }
  setItem(key: string, value: string): void {
    this.store[key] = value;
  }
}

describe('AuthService', () => {
  let service: AuthService;
  let httpTesting: HttpTestingController;
  let mockStorage: MockStorage;

  beforeEach(() => {
    mockStorage = new MockStorage();
    Object.defineProperty(window, 'localStorage', {
      value: mockStorage,
      writable: true,
    });

    TestBed.configureTestingModule({
      providers: [
        AuthService,
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([{ path: 'login', component: class {} }]),
      ],
    });

    service = TestBed.inject(AuthService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
    mockStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
    expect(service.isAuthenticated()).toBe(false);
  });

  it('should login and set session', () => {
    const mockResponse = {
      accessToken: 'jwt-test-token',
      user: {
        id: 'u-123',
        username: 'alice',
        email: 'alice@example.com',
        createdAt: '2026-09-23T00:00:00Z',
      },
    };

    service.login({ email: 'alice@example.com', password: 'password123' }).subscribe((res) => {
      expect(res.accessToken).toBe('jwt-test-token');
      expect(res.user.username).toBe('alice');
    });

    const req = httpTesting.expectOne('/api/auth/login');
    expect(req.request.method).toBe('POST');
    req.flush(mockResponse);

    expect(service.token()).toBe('jwt-test-token');
    expect(service.currentUser()?.username).toBe('alice');
    expect(service.isAuthenticated()).toBe(true);
    expect(mockStorage.getItem('chat_access_token')).toBe('jwt-test-token');
  });

  it('should handle login error and set error message', () => {
    const errorBody = {
      error: {
        code: 'INVALID_CREDENTIALS',
        message: 'Invalid email or password',
      },
    };

    service.login({ email: 'alice@example.com', password: 'wrong' }).subscribe({
      error: (err) => {
        expect(err.status).toBe(401);
      },
    });

    const req = httpTesting.expectOne('/api/auth/login');
    req.flush(errorBody, { status: 401, statusText: 'Unauthorized' });

    expect(service.errorMessage()).toBe('Invalid email or password');
    expect(service.isAuthenticated()).toBe(false);
  });

  it('should logout and clear state', () => {
    mockStorage.setItem('chat_access_token', 'sample-token');
    service.token.set('sample-token');
    service.currentUser.set({
      id: 'u-123',
      username: 'alice',
      email: 'alice@example.com',
      createdAt: '2026-09-23T00:00:00Z',
    });

    service.logout();

    expect(service.token()).toBeNull();
    expect(service.currentUser()).toBeNull();
    expect(service.isAuthenticated()).toBe(false);
    expect(mockStorage.getItem('chat_access_token')).toBeNull();
  });
});
