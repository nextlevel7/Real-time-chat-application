import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ChatMessage } from '../../features/rooms/models/message.models';
import { WebSocketService } from './websocket.service';

@Injectable({
  providedIn: 'root',
})
export class MessageService {
  private readonly http = inject(HttpClient);
  private readonly wsService = inject(WebSocketService);

  readonly messageStream$: Observable<ChatMessage> = this.wsService.onMessage();

  fetchHistory(roomId: string, limit = 50): Observable<{ messages: ChatMessage[] }> {
    return this.http.get<{ messages: ChatMessage[] }>(
      `/api/rooms/${roomId}/messages?limit=${limit}`,
    );
  }

  sendMessage(roomId: string, content: string): Observable<{ message: ChatMessage }> {
    return this.http.post<{ message: ChatMessage }>(
      `/api/rooms/${roomId}/messages`,
      { content },
    );
  }

  sendRealtimeMessage(roomId: string, content: string): void {
    this.wsService.sendMessage(roomId, content);
  }
}
