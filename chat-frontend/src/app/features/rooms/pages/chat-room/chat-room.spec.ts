import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { AuthService } from '../../../auth/services/auth.service';
import { RoomService } from '../../services/room.service';
import { ChatRoom } from './chat-room';

describe('ChatRoom', () => {
  let component: ChatRoom;
  let fixture: ComponentFixture<ChatRoom>;
  let httpTesting: HttpTestingController;

  const mockRoom = {
    id: 'room-123',
    name: 'General',
    createdBy: 'u-1',
    createdAt: '2026-09-23T00:00:00Z',
    isMember: true,
  };

  const mockMessages = [
    {
      id: 'm-1',
      roomId: 'room-123',
      senderId: 'u-1',
      senderUsername: 'alice',
      content: 'Welcome to General!',
      createdAt: '2026-09-23T00:00:00Z',
    },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatRoom],
      providers: [
        RoomService,
        AuthService,
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: {
                get: (key: string) => (key === 'id' ? 'room-123' : null),
              },
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ChatRoom);
    component = fixture.componentInstance;
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('should initialize and load room details and message history', () => {
    fixture.detectChanges();

    const roomReq = httpTesting.expectOne('/api/rooms/room-123');
    expect(roomReq.request.method).toBe('GET');
    roomReq.flush({ room: mockRoom });

    const msgReq = httpTesting.expectOne('/api/rooms/room-123/messages?limit=50');
    expect(msgReq.request.method).toBe('GET');
    msgReq.flush({ messages: mockMessages });

    const membersReq = httpTesting.expectOne('/api/rooms/room-123/members');
    expect(membersReq.request.method).toBe('GET');
    membersReq.flush({ members: [] });

    expect(component.room()?.name).toBe('General');
    expect(component.messages().length).toBe(1);
    expect(component.messages()[0].content).toBe('Welcome to General!');
    expect(component.isLoading()).toBe(false);
  });

  it('should send a message and append it to local timeline', () => {
    fixture.detectChanges();

    httpTesting.expectOne('/api/rooms/room-123').flush({ room: mockRoom });
    httpTesting.expectOne('/api/rooms/room-123/messages?limit=50').flush({ messages: [] });
    httpTesting.expectOne('/api/rooms/room-123/members').flush({ members: [] });

    component.messageForm.controls.content.setValue('New announcement');
    component.onSendMessage();

    const sendReq = httpTesting.expectOne('/api/rooms/room-123/messages');
    expect(sendReq.request.method).toBe('POST');
    expect(sendReq.request.body).toEqual({ content: 'New announcement' });

    sendReq.flush({
      message: {
        id: 'm-2',
        roomId: 'room-123',
        senderId: 'u-1',
        senderUsername: 'alice',
        content: 'New announcement',
        createdAt: '2026-09-23T00:01:00Z',
      },
    });

    expect(component.messages().length).toBe(1);
    expect(component.messages()[0].content).toBe('New announcement');
    expect(component.messageForm.controls.content.value).toBe('');
  });
});
