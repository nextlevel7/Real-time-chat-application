import { CommonModule } from '@angular/common';
import { Component, ElementRef, effect, inject, OnDestroy, OnInit, signal, ViewChild } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatToolbarModule } from '@angular/material/toolbar';
import { Subscription } from 'rxjs';
import { MessageService } from '../../../../core/services/message.service';
import { WebSocketService } from '../../../../core/services/websocket.service';
import { AuthService } from '../../../auth/services/auth.service';
import { ChatMessage } from '../../models/message.models';
import { Room, RoomMember } from '../../models/room.models';
import { RoomService } from '../../services/room.service';

@Component({
  selector: 'app-chat-room',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatToolbarModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatChipsModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './chat-room.html',
  styleUrl: './chat-room.scss',
})
export class ChatRoom implements OnInit, OnDestroy {
  @ViewChild('messagesScroll') private messagesScroll?: ElementRef<HTMLDivElement>;

  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly roomService = inject(RoomService);
  private readonly messageService = inject(MessageService);
  private readonly authService = inject(AuthService);
  private readonly wsService = inject(WebSocketService);

  private readonly subs: Subscription[] = [];
  private typingTimeout: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    effect(() => {
      const user = this.currentUser();
      if (user?.username) {
        this.activeUsers.update((users) =>
          users.includes(user.username) ? users : [...users, user.username],
        );
      }
    });
  }

  readonly currentUser = this.authService.currentUser;
  readonly isConnected = this.wsService.isConnected;

  roomId = '';
  readonly room = signal<Room | null>(null);
  readonly members = signal<RoomMember[]>([]);
  readonly activeUsers = signal<string[]>([]);
  readonly showParticipants = signal<boolean>(true);
  readonly messages = signal<ChatMessage[]>([]);
  readonly isLoading = signal<boolean>(true);
  readonly isSending = signal<boolean>(false);
  readonly errorMessage = signal<string | null>(null);
  readonly typingText = signal<string | null>(null);

  readonly messageForm = new FormGroup({
    content: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.maxLength(2000)],
    }),
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      this.router.navigate(['/']);
      return;
    }
    this.roomId = id;
    this.loadRoomData();
    this.initWebSocket();
  }

  ngOnDestroy(): void {
    if (this.roomId) {
      this.wsService.sendTyping(this.roomId, false);
      this.wsService.leaveRoom(this.roomId);
    }
    this.subs.forEach((s) => s.unsubscribe());
    if (this.typingTimeout) {
      clearTimeout(this.typingTimeout);
    }
  }

  loadRoomData(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.roomService.fetchRoom(this.roomId).subscribe({
      next: (res) => {
        this.room.set(res.room);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(err.error?.error?.message || 'Failed to load room.');
      },
    });

    this.fetchMessages();
    this.fetchMembers();
  }

  fetchMessages(): void {
    this.messageService.fetchHistory(this.roomId).subscribe({
      next: (res) => {
        this.messages.set(res.messages || []);
        this.isLoading.set(false);
        this.scrollToBottom();
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(err.error?.error?.message || 'Failed to load messages.');
      },
    });
  }

  fetchMembers(): void {
    this.roomService.fetchMembers(this.roomId).subscribe({
      next: (res) => {
        const memberList = res.members || [];
        this.members.set(memberList);
        const currentName = this.currentUser()?.username;
        if (currentName) {
          this.activeUsers.update((users) =>
            users.includes(currentName) ? users : [...users, currentName],
          );
        }
      },
      error: () => {
        // Non-critical member list failure
      },
    });
  }

  initWebSocket(): void {
    this.wsService.connect();
    this.wsService.joinRoom(this.roomId);

    this.subs.push(
      this.messageService.messageStream$.subscribe((msg) => {
        if (msg.roomId === this.roomId) {
          const isOwn = this.currentUser()?.id === msg.senderId;
          const decoratedMsg: ChatMessage = { ...msg, isNew: !isOwn };

          this.messages.update((existing) => {
            if (!existing.some((m) => m.id === msg.id)) {
              return [...existing, decoratedMsg];
            }
            return existing;
          });
          this.scrollToBottom();
        }
      }),

      this.wsService.onActiveUsers().subscribe((evt) => {
        if (evt.roomId === this.roomId && evt.users) {
          this.activeUsers.set(evt.users);
          this.members.update((existing) => {
            const updated = [...existing];
            for (const username of evt.users) {
              if (!updated.some((m) => m.username === username)) {
                updated.push({
                  id: username,
                  username,
                  email: '',
                  joinedAt: new Date().toISOString(),
                });
              }
            }
            return updated;
          });
          this.roomService.fetchMembers(this.roomId).subscribe({
            next: (res) => {
              if (res.members) {
                this.members.set(res.members);
              }
            },
          });
        }
      }),

      this.wsService.onUserJoined().subscribe((evt) => {
        if (evt.roomId === this.roomId && evt.username) {
          this.activeUsers.update((users) => {
            if (!users.includes(evt.username)) {
              return [...users, evt.username];
            }
            return users;
          });
          this.members.update((existing) => {
            if (!existing.some((m) => m.username === evt.username)) {
              return [
                ...existing,
                {
                  id: evt.username,
                  username: evt.username,
                  email: '',
                  joinedAt: new Date().toISOString(),
                },
              ];
            }
            return existing;
          });
          this.roomService.fetchMembers(this.roomId).subscribe({
            next: (res) => {
              if (res.members) {
                this.members.set(res.members);
              }
            },
          });
        }
      }),

      this.wsService.onUserLeft().subscribe((evt) => {
        if (evt.roomId === this.roomId && evt.username) {
          this.activeUsers.update((users) => users.filter((u) => u !== evt.username));
        }
      }),

      this.wsService.onTyping().subscribe((evt) => {
        if (evt.roomId === this.roomId && evt.username !== this.currentUser()?.username) {
          if (evt.isTyping) {
            this.typingText.set(`${evt.username} is typing...`);
          } else {
            this.typingText.set(null);
          }
        }
      }),

      this.wsService.onError().subscribe((err) => {
        this.errorMessage.set(err.message || 'Real-time error occurred.');
      }),
    );
  }

  onTypingInput(): void {
    if (!this.roomId) return;
    this.wsService.sendTyping(this.roomId, true);

    if (this.typingTimeout) {
      clearTimeout(this.typingTimeout);
    }
    this.typingTimeout = setTimeout(() => {
      this.wsService.sendTyping(this.roomId, false);
    }, 2000);
  }

  onSendMessage(): void {
    if (this.messageForm.invalid || this.isSending()) return;

    const content = this.messageForm.controls.content.value.trim();
    if (!content) return;

    if (this.typingTimeout) {
      clearTimeout(this.typingTimeout);
    }
    this.wsService.sendTyping(this.roomId, false);

    // If socket connected, emit via real-time WebSocket
    if (this.wsService.isConnected()) {
      this.messageService.sendRealtimeMessage(this.roomId, content);
      this.messageForm.reset();
      return;
    }

    // Fallback to REST if socket is not currently connected
    this.isSending.set(true);
    this.messageService.sendMessage(this.roomId, content).subscribe({
      next: (res) => {
        this.messages.update((existing) => [...existing, res.message]);
        this.messageForm.reset();
        this.isSending.set(false);
        this.scrollToBottom();
      },
      error: (err) => {
        this.isSending.set(false);
        this.errorMessage.set(err.error?.error?.message || 'Failed to send message.');
      },
    });
  }

  toggleParticipants(): void {
    this.showParticipants.update((v) => !v);
  }

  isUserActive(username: string): boolean {
    return this.activeUsers().includes(username);
  }

  onLeaveRoom(): void {
    this.roomService.leaveRoom(this.roomId).subscribe({
      next: () => {
        this.router.navigate(['/']);
      },
      error: (err) => {
        this.errorMessage.set(err.error?.error?.message || 'Failed to leave room.');
      },
    });
  }

  onBack(): void {
    this.router.navigate(['/']);
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.messagesScroll) {
        this.messagesScroll.nativeElement.scrollTop =
          this.messagesScroll.nativeElement.scrollHeight;
      }
    }, 50);
  }
}
