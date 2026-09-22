export interface Room {
  id: string;
  name: string;
  createdBy: string;
  createdAt: string;
  isMember?: boolean;
}

export interface RoomMember {
  id: string;
  username: string;
  email: string;
  joinedAt: string;
}

export interface CreateRoomPayload {
  name: string;
}
