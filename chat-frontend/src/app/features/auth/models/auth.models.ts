import { User } from '../../../core/models/user.model';

export interface AuthResponse {
  accessToken: string;
  user: User;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

export type { ApiErrorResponse, User } from '../../../core/models/user.model';
