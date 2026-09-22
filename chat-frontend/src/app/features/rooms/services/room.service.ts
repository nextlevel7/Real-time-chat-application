import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { catchError, Observable, tap, throwError } from 'rxjs';
import { CreateRoomPayload, Room, RoomMember } from '../models/room.models';

@Injectable({
  providedIn: 'root',
})
export class RoomService {
  private readonly http = inject(HttpClient);

  readonly rooms = signal<Room[]>([]);
  readonly isLoading = signal<boolean>(false);
  readonly errorMessage = signal<string | null>(null);

  fetchRooms(): Observable<{ rooms: Room[] }> {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    return this.http.get<{ rooms: Room[] }>('/api/rooms').pipe(
      tap((res) => {
        this.rooms.set(res.rooms);
        this.isLoading.set(false);
      }),
      catchError((err: HttpErrorResponse) => {
        this.isLoading.set(false);
        const msg = err.error?.error?.message || 'Failed to load chat rooms.';
        this.errorMessage.set(msg);
        return throwError(() => err);
      }),
    );
  }

  createRoom(payload: CreateRoomPayload): Observable<{ room: Room }> {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    return this.http.post<{ room: Room }>('/api/rooms', payload).pipe(
      tap((res) => {
        this.rooms.update((existing) => [res.room, ...existing]);
        this.isLoading.set(false);
      }),
      catchError((err: HttpErrorResponse) => {
        this.isLoading.set(false);
        const msg = err.error?.error?.message || 'Failed to create room.';
        this.errorMessage.set(msg);
        return throwError(() => err);
      }),
    );
  }

  joinRoom(roomId: string): Observable<{ status: string }> {
    this.errorMessage.set(null);

    return this.http.post<{ status: string }>(`/api/rooms/${roomId}/join`, {}).pipe(
      tap(() => {
        this.rooms.update((rooms) =>
          rooms.map((r) => (r.id === roomId ? { ...r, isMember: true } : r)),
        );
      }),
      catchError((err: HttpErrorResponse) => {
        const msg = err.error?.error?.message || 'Failed to join room.';
        this.errorMessage.set(msg);
        return throwError(() => err);
      }),
    );
  }

  leaveRoom(roomId: string): Observable<{ status: string }> {
    this.errorMessage.set(null);

    return this.http.post<{ status: string }>(`/api/rooms/${roomId}/leave`, {}).pipe(
      tap(() => {
        this.rooms.update((rooms) =>
          rooms.map((r) => (r.id === roomId ? { ...r, isMember: false } : r)),
        );
      }),
      catchError((err: HttpErrorResponse) => {
        const msg = err.error?.error?.message || 'Failed to leave room.';
        this.errorMessage.set(msg);
        return throwError(() => err);
      }),
    );
  }

  fetchRoom(roomId: string): Observable<{ room: Room }> {
    return this.http.get<{ room: Room }>(`/api/rooms/${roomId}`);
  }

  fetchMembers(roomId: string): Observable<{ members: RoomMember[] }> {
    return this.http.get<{ members: RoomMember[] }>(`/api/rooms/${roomId}/members`);
  }
}
