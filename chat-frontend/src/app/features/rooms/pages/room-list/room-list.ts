import { CommonModule } from '@angular/common';
import { Component, inject, OnInit } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatToolbarModule } from '@angular/material/toolbar';
import { WebSocketService } from '../../../../core/services/websocket.service';
import { AuthService } from '../../../auth/services/auth.service';
import { RoomService } from '../../services/room.service';

@Component({
  selector: 'app-room-list',
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
  templateUrl: './room-list.html',
  styleUrl: './room-list.scss',
})
export class RoomList implements OnInit {
  private readonly authService = inject(AuthService);
  private readonly roomService = inject(RoomService);
  private readonly router = inject(Router);
  private readonly wsService = inject(WebSocketService);

  readonly currentUser = this.authService.currentUser;
  readonly rooms = this.roomService.rooms;
  readonly isLoading = this.roomService.isLoading;
  readonly errorMessage = this.roomService.errorMessage;

  readonly createForm = new FormGroup({
    name: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.minLength(1), Validators.maxLength(100)],
    }),
  });

  ngOnInit(): void {
    this.roomService.fetchRooms().subscribe();
  }

  onCreateRoom(): void {
    if (this.createForm.invalid) {
      this.createForm.markAllAsTouched();
      return;
    }

    const name = this.createForm.controls.name.value.trim();
    if (!name) return;

    this.roomService.createRoom({ name }).subscribe({
      next: () => {
        this.createForm.reset();
      },
    });
  }

  onJoin(roomId: string): void {
    this.roomService.joinRoom(roomId).subscribe();
  }

  onLeave(roomId: string): void {
    this.roomService.leaveRoom(roomId).subscribe();
  }

  onOpenRoom(roomId: string): void {
    this.router.navigate(['/rooms', roomId]);
  }

  onLogout(): void {
    this.wsService.disconnect();
    this.authService.logout();
  }
}
