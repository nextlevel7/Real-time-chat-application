import { inject, Injectable, signal } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { io, Socket } from 'socket.io-client';
import { AuthService } from '../../features/auth/services/auth.service';
import { ChatMessage } from '../../features/rooms/models/message.models';

export interface SocketError {
  code: string;
  message: string;
}

export interface UserEvent {
  roomId: string;
  username: string;
}

export interface TypingEvent {
  roomId: string;
  username: string;
  isTyping: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class WebSocketService {
  private readonly authService = inject(AuthService);
  private socket: Socket | null = null;

  readonly isConnected = signal<boolean>(false);

  private readonly message$ = new Subject<ChatMessage>();
  private readonly userJoined$ = new Subject<UserEvent>();
  private readonly userLeft$ = new Subject<UserEvent>();
  private readonly typing$ = new Subject<TypingEvent>();
  private readonly error$ = new Subject<SocketError>();

  connect(): void {
    const token = this.authService.token();
    if (!token) return;

    if (this.socket && this.socket.connected) {
      return;
    }

    // Connect using same host/port via proxy /socket.io
    this.socket = io({
      path: '/socket.io',
      auth: { token },
      transports: ['polling', 'websocket'],
      autoConnect: true,
    });

    this.socket.on('connect', () => {
      this.isConnected.set(true);
    });

    this.socket.on('disconnect', () => {
      this.isConnected.set(false);
    });

    this.socket.on('receive_message', (msg: ChatMessage) => {
      this.message$.next(msg);
    });

    this.socket.on('user_joined', (event: UserEvent) => {
      this.userJoined$.next(event);
    });

    this.socket.on('user_left', (event: UserEvent) => {
      this.userLeft$.next(event);
    });

    this.socket.on('user_typing', (event: TypingEvent) => {
      this.typing$.next(event);
    });

    this.socket.on('error', (err: SocketError) => {
      this.error$.next(err);
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected.set(false);
    }
  }

  joinRoom(roomId: string): void {
    this.ensureConnected();
    this.socket?.emit('join_room', { roomId });
  }

  leaveRoom(roomId: string): void {
    this.socket?.emit('leave_room', { roomId });
  }

  sendMessage(roomId: string, content: string): void {
    this.ensureConnected();
    this.socket?.emit('send_message', { roomId, content });
  }

  sendTyping(roomId: string, isTyping: boolean): void {
    this.socket?.emit('typing', { roomId, isTyping });
  }

  onMessage(): Observable<ChatMessage> {
    return this.message$.asObservable();
  }

  onUserJoined(): Observable<UserEvent> {
    return this.userJoined$.asObservable();
  }

  onUserLeft(): Observable<UserEvent> {
    return this.userLeft$.asObservable();
  }

  onTyping(): Observable<TypingEvent> {
    return this.typing$.asObservable();
  }

  onError(): Observable<SocketError> {
    return this.error$.asObservable();
  }

  private ensureConnected(): void {
    if (!this.socket || !this.socket.connected) {
      this.connect();
    }
  }
}
