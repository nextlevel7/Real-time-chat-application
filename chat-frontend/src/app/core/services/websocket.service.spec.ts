import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { AuthService } from '../../features/auth/services/auth.service';
import { WebSocketService } from './websocket.service';

describe('WebSocketService', () => {
  let service: WebSocketService;
  let mockAuthService: { token: ReturnType<typeof signal<string | null>> };

  beforeEach(() => {
    mockAuthService = {
      token: signal<string | null>('fake-jwt-token'),
    };

    TestBed.configureTestingModule({
      providers: [
        WebSocketService,
        { provide: AuthService, useValue: mockAuthService },
      ],
    });

    service = TestBed.inject(WebSocketService);
  });

  afterEach(() => {
    service.disconnect();
  });

  it('should initialize with disconnected state', () => {
    expect(service.isConnected()).toBe(false);
  });

  it('should not connect if auth token is null', () => {
    mockAuthService.token.set(null);
    service.connect();
    expect(service.isConnected()).toBe(false);
  });

  it('should provide observables for real-time socket events', () => {
    expect(service.onMessage()).toBeDefined();
    expect(service.onUserJoined()).toBeDefined();
    expect(service.onUserLeft()).toBeDefined();
    expect(service.onTyping()).toBeDefined();
    expect(service.onError()).toBeDefined();
  });

  it('should emit socket actions safely without throwing when disconnected', () => {
    expect(() => service.joinRoom('room-1')).not.toThrow();
    expect(() => service.leaveRoom('room-1')).not.toThrow();
    expect(() => service.sendMessage('room-1', 'hi')).not.toThrow();
    expect(() => service.sendTyping('room-1', true)).not.toThrow();
  });
});
