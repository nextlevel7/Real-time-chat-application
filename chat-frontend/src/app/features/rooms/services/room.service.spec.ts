import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { RoomService } from './room.service';

describe('RoomService', () => {
  let service: RoomService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        RoomService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(RoomService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should fetch rooms and update the rooms signal', () => {
    const mockRooms = [
      { id: 'r1', name: 'General', createdBy: 'u1', createdAt: '2026-09-23T00:00:00Z', isMember: true },
    ];

    service.fetchRooms().subscribe((res) => {
      expect(res.rooms.length).toBe(1);
    });

    const req = httpTesting.expectOne('/api/rooms');
    expect(req.request.method).toBe('GET');
    req.flush({ rooms: mockRooms });

    expect(service.rooms()).toEqual(mockRooms);
    expect(service.isLoading()).toBe(false);
  });

  it('should fetch room messages', () => {
    const roomId = 'room-123';
    const mockMessages = [
      {
        id: 'm1',
        roomId,
        senderId: 'u1',
        senderUsername: 'alice',
        content: 'Hello world!',
        createdAt: '2026-09-23T00:00:00Z',
      },
    ];

    service.fetchMessages(roomId).subscribe((res) => {
      expect(res.messages).toEqual(mockMessages);
    });

    const req = httpTesting.expectOne(`/api/rooms/${roomId}/messages?limit=50`);
    expect(req.request.method).toBe('GET');
    req.flush({ messages: mockMessages });
  });

  it('should send a room message', () => {
    const roomId = 'room-123';
    const payload = { content: 'Testing message' };
    const mockMessage = {
      id: 'm2',
      roomId,
      senderId: 'u1',
      senderUsername: 'alice',
      content: 'Testing message',
      createdAt: '2026-09-23T00:01:00Z',
    };

    service.sendMessage(roomId, payload.content).subscribe((res) => {
      expect(res.message).toEqual(mockMessage);
    });

    const req = httpTesting.expectOne(`/api/rooms/${roomId}/messages`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({ message: mockMessage });
  });
});
