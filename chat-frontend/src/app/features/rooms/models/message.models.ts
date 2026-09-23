export interface ChatMessage {
  id: string;
  roomId: string;
  senderId: string;
  senderUsername: string;
  content: string;
  createdAt: string;
  isNew?: boolean;
}

export interface SendMessagePayload {
  content: string;
}
