import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatToolbarModule } from '@angular/material/toolbar';
import { AuthService } from '../../../auth/services/auth.service';

@Component({
  selector: 'app-room-list',
  imports: [CommonModule, MatToolbarModule, MatButtonModule, MatCardModule],
  templateUrl: './room-list.html',
  styleUrl: './room-list.scss',
})
export class RoomList {
  readonly authService = inject(AuthService);

  onLogout(): void {
    this.authService.logout();
  }
}
