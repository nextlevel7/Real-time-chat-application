export interface User {
  id: string;
  username: string;
  email: string;
  createdAt: string;
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
  };
}
